from twisted.internet import reactor
import csv
import utility
import logging

log = logging.getLogger(__name__)

class DiscreteEventEmitter:
    fieldnames = ()
    fieldtypes = ()
    name = ''

    def __init__(self, source_data):
        self.owner = None
        self.data = source_data
        self.previous_state = None

    def register_events(self):
        if not self.owner:
            raise Exception('owner agent not set.')
        for row in self.data:
            if self.has_changed(row):
                arrival_time = float(row[0])
                row_as_dict = {
                    self.fieldnames[ix]: self.fieldtypes[ix](value) for ix, 
                        value in enumerate(row[1:])}
                row_as_dict['type'] = self.name
                reactor.callLater(arrival_time, self.owner.handle_discrete_event, row_as_dict)
                self.previous_state = row
    
    def has_changed(self, incoming_row):
        return True


class RandomOrderEmitter(DiscreteEventEmitter):
    fieldnames = ('fundamental_price', 'price', 'buy_sell_indicator', 'time_in_force')
    fieldtypes = (float, int, str, int)
    name = 'investor_arrivals'

class ELOSpeedChangeEmitter(DiscreteEventEmitter):
    fieldnames = ('technology_on',)
    fieldtypes = (bool, )
    name = 'speed_change'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous_state = (0, False)

    def has_changed(self, incoming_row):
        return not (self.previous_state[1] == incoming_row[1])

class ELOSliderChangeEmitter(DiscreteEventEmitter):
    fieldnames = ('slider_a_x', 'slider_a_y', 'slider_a_z')
    fieldtypes = (float, float, float)
    name = 'slider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous_state = (0., 0., 0., 0.)

    def has_changed(self, incoming_row):
        return not (self.previous_state[1:] == incoming_row[1:])
