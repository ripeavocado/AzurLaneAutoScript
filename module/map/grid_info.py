from module.base.utils import location2node
from module.logger import logger


class GridInfo:
    """
    Class that gather basic information of a grid in map_v1.

    Visit 碧蓝航线WIKI(Chinese Simplified) http://wiki.joyme.com/blhx, to get basic info of a map_v1. For example,
    visit http://wiki.joyme.com/blhx/7-2, to know more about campaign 7-2, which includes boss point, enemy spawn point.

    A grid contains these unchangeable properties which can known from WIKI.
    | print_name | property_name  | description             |
    |------------|----------------|-------------------------|
    | ++         | is_land        | fleet can't go to land  |
    | --         | is_sea         | sea                     |
    | __         |                | submarine spawn point   |
    | SP         | is_spawn_point | fleet may spawns here   |
    | ME         | may_enemy      | enemy may spawns here   |
    | MB         | may_boss       | boss may spawns here    |
    | MM         | may_mystery    | mystery may spawns here |
    | MA         | may_ammo       | fleet can get ammo here |
    | MS         | may_siren      | Siren/Elite enemy spawn |
    """

    # is_sea --
    is_land = False  # ++
    is_spawn_point = False  # SP

    may_enemy = False  # ME
    may_boss = False  # MB
    may_mystery = False  # MM
    may_ammo = False  # MA
    may_siren = False  # MS

    is_enemy = False  # example: 0L 1M 2C 3T 3E
    is_boss = False  # BO
    is_mystery = False  # MY
    is_ammo = False  # AM
    is_fleet = False  # FL
    is_submarine = False  # SS
    is_siren = False  # SI

    enemy_scale = 0
    enemy_type = 'Enemy'  # Light, Main, Carrier, Treasure, Enemy(unknown)

    is_cleared = False
    is_ambush_save = False
    cost = 9999
    connection = None
    weight = 1

    location = None

    def decode(self, text):
        dic = {
            '++': 'is_land',
            'SP': 'is_spawn_point',
            'ME': 'may_enemy',
            'MB': 'may_boss',
            'MM': 'may_mystery',
            'MA': 'may_ammo',
            'MS': 'may_siren',
        }
        if text in dic:
            self.__setattr__(dic[text], True)
        if self.may_enemy or self.may_boss or self.may_mystery or self.may_mystery:
            self.is_ambush_save = True
        if self.may_siren:
            self.may_enemy = True
        if self.may_boss:
            self.may_enemy = True

    def encode(self):
        dic = {
            '++': 'is_land',
            'BO': 'is_boss',
            'SI': 'is_siren'
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        if self.is_enemy:
            # if self.may_siren:
            #     return 'SI'
            # else:
            return '%s%s' % (self.enemy_scale, self.enemy_type[0].upper())

        dic = {
            'FL': 'is_fleet',
            'MY': 'is_mystery',
            'AM': 'is_ammo',
            '==': 'is_cleared'
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        return '--'

    def __str__(self):
        return location2node(self.location)

    @property
    def str(self):
        return self.encode()

    @property
    def is_sea(self):
        return False if self.is_land or self.is_enemy or self.is_mystery or self.is_boss else True

    @property
    def is_accessible(self):
        return self.cost < 9999

    @property
    def is_nearby(self):
        return self.cost < 20

    def update(self, info):
        """
        Args:
            info(GridInfo):
        """
        # failure = 0
        for item in ['boss', 'siren']:
            if info.__getattribute__('is_' + item):
                if self.__getattribute__('may_' + item) and not self.is_cleared \
                        and not info.is_fleet and not self.is_fleet:
                    self.__setattr__('is_' + item, True)
                    return True
                else:
                    logger.info(f'Wrong Prediction. Grid: {self}, Attr: {item}')
                    # failure += 1

        if info.is_enemy and self.may_enemy and not self.is_cleared \
                and not info.is_fleet and not self.is_fleet:
            self.is_enemy = True
            self.enemy_scale = info.enemy_scale
            self.enemy_type = info.enemy_type
            if self.may_siren:
                self.is_siren = True
            return True

        for item in ['mystery', 'ammo']:
            if info.__getattribute__('is_' + item):
                if self.__getattribute__('may_' + item):
                    self.__setattr__('is_' + item, True)
                    return True
                else:
                    logger.info(f'Wrong Prediction. Grid: {self}, Attr: {item}')
                    # failure += 1

        self.is_fleet = info.is_fleet
        return False

    def wipe_out(self):
        self.is_enemy = False
        self.enemy_scale = 0
        self.enemy_type = 'Enemy'
        self.is_mystery = False
        self.is_boss = False
        self.is_ammo = False
        self.is_siren = False