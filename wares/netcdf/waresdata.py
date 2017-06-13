from lmtdata import LMTData

class WaresData(LMTData):
    def __init__(self, ncvariables):
        self.variables = ncvariables
        self.make_data(ncvariables)

    def make_data(self, ncvariables):
        """Make the actual Wares data"""
        datas = [name for name in ncvariables.keys() if name.find('Data') == 0]
        for d in datas:
            data_type = d.split('.')[1]
            self[data_type] = []
        for data_type in self.keys():
            keys = [name.split('.')[-1] for name in ncvariables.keys() if name.find('Data.%s.' % data_type) == 0]
            for key in keys:
                try:
                    #self.__setattr__(key, ncvariables['Data.%s.%s' % (data_type, key)].get())
                    self.__setattr__(key, ncvariables['Data.%s.%s' % (data_type, key)][:])
                    self[data_type].append(key)
                except:
                    self.__setattr__(key, None)
