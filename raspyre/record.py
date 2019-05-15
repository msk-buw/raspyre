"""
The Record object stores an arbitrary number of measured values. All records have the "time" attribute in common, that has the time of creation of the object in system time. Record objects can be sorted by this property. Element acces is done as in dictionarys.

"""
import time

class Record(object) :
    def __init__(self, values = None):
        self.values = {}
        if values:
            self.values = values
        self.values['time'] = time.time()
    def add(self, key, value) :
        self.values[key] = value
    def get(self, key) :
        return self.values[key]


    def __cmp__ (self, other):
        return self[timestamp] > other[timestamp]
    
     # this code comes from http://www.rafekettler.com/magicmethods.html#sequence
     # "magic methods" to make the Record object be iterable
    def __len__(self):
        return len(self.values)

    def __getitem__(self, key):
        # if key is of invalid type or value, the list values will raise the error
        if key in ['time' , 'timestamp']:
            return self.values['time']
        else:
            return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __delitem__(self, key):
        del self.values[key]

    def __iter__(self):
        return iter(self.values)

    def __repr__(self):
        repr_str = "Record("
        for k, v in sorted(self.values.items()):
            repr_str += "%s: %s, " % (str(k), str(v))
        repr_str += ")"
        return repr_str
