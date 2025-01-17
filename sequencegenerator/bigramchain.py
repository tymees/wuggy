import codecs
import random
from collections import defaultdict, namedtuple

Link=namedtuple('Link',['position','value'])

class BigramChain(defaultdict):
    """A dictionary storing the next possible value, given a list of input sequences."""
    def __init__(self, plugin_module, data=None, encoding='utf-8', size=100, cutoff=1, token=False):
        defaultdict.__init__(self, dict)
        self.plugin_module=plugin_module
        try:
            self.hidden_sequence=self.plugin_module.hidden_sequence
        except AttributeError:
            self.hidden_sequence=False
        if data!=None:
            self.load(data, size=size, cutoff=cutoff, token=token)
        self.startkeys=[]
        self.status={'message':'','progress':0}
        self.subscribers=[]
        self.limit_frequencies={}

    def set_status(self, message, progress):
        for receiver in [self]+self.subscribers:
            receiver.status['message']=message
            receiver.status['progress']=progress

    def clear_status(self):
        for receiver in [self]+self.subscribers:
            receiver.status['message']=''
            receiver.status['progress']=0

    def load(self, datafile, size=100, cutoff=1, token=False):
        lines=datafile.readlines()
        nlines=float(len(lines))
        for i,line in enumerate(lines):
            if i % 1000==0:
                self.set_status("Constructing Bigram Chain", i/nlines*100)
            fields=line.strip('\n\t').split(self.plugin_module.separator)
            reference, input_sequence, frequency=fields
            frequency=float(frequency) if token==True else 1
            frequency=1
            sequence=(self.plugin_module.transform(input_sequence, frequency))
            n=len(sequence.representation)
            if frequency>=cutoff and random.randint(1,100)<=size:
                for i in range(n):
                    key=Link(i,sequence.representation[i])
                    if i+1<n:
                        next_key=Link(i+1,sequence.representation[i+1])
                        self[key][next_key]=self[key].get(next_key,0)+sequence.frequency
            else:
                pass
        datafile.close()
        self.clear_status()
        self.set_startkeys()

    def set_startkeys(self, reference_sequence=None, fields=None):
        if fields==None:
            fields=self.plugin_module.default_fields
        if reference_sequence==None:
            self.startkeys=dict([(key,0) for key in self.keys() if key.position==0])
        else:
            reference_values=[reference_sequence[0].__getattribute__(field) for field in fields]
            self.startkeys={}
            for key in self.keys():
                if key.position==0:
                    self.startkeys[key]=0

    def get_frequencies(self,reference_sequence):
        frequencies={}
        for position in range(len(reference_sequence)-1):
            key=Link(position, reference_sequence[position])
            nextkey=Link(position+1, reference_sequence[position+1])
            try:
                frequency=self[key][nextkey]
            except KeyError:
                frequency=0
            frequencies[position]=frequency
        return frequencies

    def build_limit_frequencies(self, fields):
        limits=defaultdict(dict)
        for key, nextkeys in self.iteritems():
            position, value=key
            subkey_a=(position, tuple([value.__getattribute__(field) for field in fields]))
            for nextkey,frequency in nextkeys.iteritems():
                position,value=nextkey
                subkey_b=(position, tuple([value.__getattribute__(field) for field in fields]))
                subkey=(subkey_a,subkey_b)
                minfrequency=limits[subkey].get('min',frequency)
                limits[subkey]['min']=min(minfrequency,frequency)
                maxfrequency=limits[subkey].get('max',frequency)
                limits[subkey]['max']=max(maxfrequency,frequency)
        self.limit_frequencies[tuple(fields)]=limits

    def frequency_filter(self, reference_sequence, lower, upper, kind='dev'):
        result=BigramChain(self.plugin_module)
        frequencies=self.get_frequencies(reference_sequence)
        for key, nextkeys in self.items():
            try:
                if kind=='dev':
                    minfreq=frequencies[key.position]-lower
                    maxfreq=frequencies[key.position]+upper
                elif kind=='limit':
                    minfreq=lower
                    maxfreq=upper
            except:
                pass
            else:
                for nextkey,frequency in nextkeys.items():
                    if minfreq<=frequency<=maxfreq:
                        result[key][nextkey]=frequency
                        # print 'set %s %s to %d because %d <= %d <= %d' % (key,nextkey,frequency,minfreq,frequency,maxfreq)
                        # print result
        result=result.clean(len(reference_sequence)-1)
        result.set_startkeys()
        return result

    def segmentset_filter(self, reference_sequence, segmentset):
        segmentset=segmentset.union(set(('^','$')))
        result=BigramChain(self.plugin_module)
        for key, nextkeys in self.items():
            if key.value.letters in segmentset:
                for nextkey, frequency in nextkeys.items():
                    if nextkey.value.letters in segmentset:
                        result[key][nextkey]=frequency
        result=result.clean(len(reference_sequence)-1)
        result.set_startkeys()
        return result

    def attribute_filter(self, reference_sequence, attribute):
        result=BigramChain(self.plugin_module)
        if type(reference_sequence[0])==self.plugin_module.Segment:
            for key,nextkeys in self.items():
                try:
                    if key.value.__getattribute__(attribute) == reference_sequence[key.position].__getattribute__(attribute):
                        result[key]=self[key]
                except IndexError:
                    pass
        else:
            for key,nextkeys in self.items():
                try:
                    if key.value.__getattribute__(attribute) == reference_sequence[key.position]:
                        result[key]=self[key]
                except IndexError:
                    pass
        return result

    def clean(self, maxpos):
        """Remove chains that can not be completed.
        """
        n=len(self)
        result=BigramChain(self.plugin_module)
        for key, nextkeys in self.items():
            for nextkey, frequency in nextkeys.items():
                if nextkey in self or nextkey.position==maxpos:
                    result[key][nextkey]=frequency
        if len(self)==len(result):
            return result
        else:
            return result.clean(maxpos)

    def generate(self, startkeys=None):
        if startkeys==None:
            startkeys=self.startkeys
        startkeys=list(startkeys.iteritems())
        random.shuffle(startkeys)
        startkeys=dict(startkeys)
        if len(self)>0:
            for key in startkeys:
                if key not in self:
                    yield (key.value,)
                else:
                    next_keys=self[key]
                    for result in self.generate(next_keys):
                        yield (key.value,)+result
        else:
            raise Exception('LinkError')

    def display(self):
        for key, nextkeys in sorted(self.items(),key=lambda x:x):
            print '***',key.position,key.value
            for nextkey,frequency in nextkeys.items():
                print nextkey.value,frequency
