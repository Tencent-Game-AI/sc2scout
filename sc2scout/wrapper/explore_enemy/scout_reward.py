from sc2scout.envs import scout_macro as sm

ARRIVED_DIST_GAP = 4

class Reward(object):
    def __init__(self, w):
        self.w = w
        self.rwd = 0

    def reset(self, obs, env):
        raise NotImplementedError

    def compute_rwd(self, obs, reward, env):
        raise NotImplementedError

class HomeReward(Reward):
    def __init__(self, back=False, negative=False):
        super(HomeReward, self).__init__(1)
        self._last_dist = None
        self._back = back
        self._negative = negative

    def reset(self, obs, env):
        self._last_dist = self._compute_dist(env)

    def compute_rwd(self, obs, reward, env):
        tmp_dist = self._compute_dist(env)
        if self._back:
            if self._negative:
                if tmp_dist > self._last_dist:
                    self.rwd = self.w * -1
                else:
                    self.rwd = 0
            else:
                if tmp_dist > self._last_dist:
                    self.rwd = self.w * -1
                elif tmp_dist < self._last_dist:
                    self.rwd = self.w * 1
                else:
                    self.rwd = 0
        else:
            if self._negative:
                if tmp_dist < self._last_dist:
                    self.rwd = self.w * -1
                else:
                    self.rwd = 0
            else:
                if tmp_dist > self._last_dist:
                    self.rwd = self.w * 1
                elif tmp_dist < self._last_dist:
                    self.rwd = self.w * -1
                else:
                    self.rwd = 0
        #print('home_rwd=', self.rwd)
        self._last_dist = tmp_dist

    def _compute_dist(self, env):
        scout = env.scout()
        home = env.owner_base()
        dist = sm.calculate_distance(scout.float_attr.pos_x, 
                                     scout.float_attr.pos_y, 
                                     home[0], home[1])
        return dist

class HomeArrivedReward(Reward):
    def __init__(self, weight=10):
        super(HomeArrivedReward, self).__init__(weight)
        self._once = False

    def reset(self, obs, env):
        self._once = False

    def compute_rwd(self, obs, reward, env):
        if self._once:
            self.rwd = 0
            return
        tmp_dist = self._compute_dist(env)
        if tmp_dist <= ARRIVED_DIST_GAP:
            self.rwd = 1 * self.w
            self._once = True
        else:
            self.rwd = 0
        print('home_arrived reward=', self.rwd)

    def _compute_dist(self, env):
        scout = env.scout()
        home = env.owner_base()
        dist = sm.calculate_distance(scout.float_attr.pos_x, 
                                     scout.float_attr.pos_y, 
                                     home[0], home[1])
        return dist

class EnemyBaseReward(Reward):
    def __init__(self, back=False, negative=False):
        super(EnemyBaseReward, self).__init__(1)
        self._last_dist = None
        self._back = back
        self._negative = negative

    def reset(self, obs, env):
        self._last_dist = self._compute_dist(env)

    def compute_rwd(self, obs, reward, env):
        tmp_dist = self._compute_dist(env)
        if self._back:
            if self._negative:
                if tmp_dist < self._last_dist:
                    self.rwd = self.w * -1
                else:
                    self.rwd = 0
            else:
                if tmp_dist < self._last_dist:
                    self.rwd = self.w * -1
                elif tmp_dist > self._last_dist:
                    self.rwd = self.w * 1
                else:
                    self.rwd = 0
        else:
            if self._negative:
                if tmp_dist > self._last_dist:
                    self.rwd = self.w * -1
                else:
                    self.rwd = 0
            else:
                if tmp_dist < self._last_dist:
                    self.rwd = self.w * 1
                elif tmp_dist > self._last_dist:
                    self.rwd = self.w * -1
                else:
                    self.rwd = 0
        self._last_dist = tmp_dist
        #print('enemy_rwd=', self.rwd)

    def _compute_dist(self, env):
        scout = env.scout()
        enemy_base = env.enemy_base()
        dist = sm.calculate_distance(scout.float_attr.pos_x, 
                                     scout.float_attr.pos_y, 
                                     enemy_base[0], enemy_base[1])
        return dist

class EnemyBaseArrivedReward(Reward):
    def __init__(self, weight=10):
        super(EnemyBaseArrivedReward, self).__init__(weight)
        self._once = False

    def reset(self, obs, env):
        self._once = False

    def compute_rwd(self, obs, reward, env):
        if self._once:
            self.rwd = 0
            return
        tmp_dist = self._compute_dist(env)
        if tmp_dist <= ARRIVED_DIST_GAP:
            self.rwd = 1 * self.w
            self._once = True
        else:
            self.rwd = 0
        #print('enemy_base_arrived reward=', self.rwd)

    def _compute_dist(self, env):
        scout = env.scout()
        enemy_base = env.enemy_base()
        dist = sm.calculate_distance(scout.float_attr.pos_x, 
                                     scout.float_attr.pos_y, 
                                     enemy_base[0], enemy_base[1])
        return dist

class ViewEnemyReward(Reward):
    def __init__(self, weight=3):
        super(ViewEnemyReward, self).__init__(weight)
        self._unit_set = set([])
        ''' the tag of enemybase will be repeatly changed while scout is nearby'''
        self._enemy_base_once = False

    def reset(self, obs, env):
        self._unit_set = set([])
        self._enemy_base_once = False

    def compute_rwd(self, obs, reward, env):
        enemy_units = []
        find_base = False
        units = obs.observation['units']
        for unit in units:
            if unit.int_attr.alliance == sm.AllianceType.ENEMY.value:
                if unit.unit_type in sm.BASE_UNITS:
                    if not self._enemy_base_once:
                        self._enemy_base_once = True
                        find_base = True
                else:
                    enemy_units.append(unit.tag)

        count = 0
        for eu in enemy_units:
            if eu in self._unit_set:
                pass
            else:
                count += 1
                self._unit_set.add(eu)
        if find_base:
            count += 1

        self.rwd = count * self.w
        #print('view enemy count=', count, ';reward=', self.rwd)

MIN_DIST_ERROR = 2.0

class MinDistReward(Reward):
    def __init__(self, negative=False):
        super(MinDistReward, self).__init__(1)
        self._min_dist = None
        self._negative = negative

    def reset(self, obs, env):
        self._min_dist = self._compute_dist(env)

    def compute_rwd(self, obs, reward, env):
        tmp_dist = self._compute_dist(env)
        if self._negative:
            if tmp_dist > self._min_dist + MIN_DIST_ERROR:
                self.rwd = self.w * -1
            else:
                self.rwd = 0
        else:
            if tmp_dist > self._min_dist + MIN_DIST_ERROR:
                self.rwd = self.w * -1
            else:
                self.rwd = self.w * 1

        if self._min_dist > tmp_dist:
            self._min_dist = tmp_dist

    def _compute_dist(self, env):
        scout = env.scout()
        home = env.owner_base()
        enemy_base = env.enemy_base()
        home_dist = sm.calculate_distance(scout.float_attr.pos_x, 
                                     scout.float_attr.pos_y, 
                                     home[0], home[1])

        enemy_dist = sm.calculate_distance(scout.float_attr.pos_x, 
                                     scout.float_attr.pos_y, 
                                     enemy_base[0], enemy_base[1])
        return (home_dist + enemy_dist)


