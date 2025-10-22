from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import collections
from collections import defaultdict
import json
import copy
import numpy as np
import pandas as pd

empty_dict = {'AMETHYSTS' : 0, 'STARFRUIT' : 0, 'ORCHIDS': 0, 'CHOCOLATE': 0, 'STRAWBERRIES': 0, 'ROSES': 0, 'GIFT_BASKET': 0, 'COCONUT': 0, 'COCONUT_COUPON': 0}

def def_value():
    return copy.deepcopy(empty_dict)

class Trader:
    sf_cache = []
    starfruit_dim = 4
    position = copy.deepcopy(empty_dict)
    # 'DIP' : 300, 'BAGUETTE': 150, 'UKULELE' : 70, 'PICNIC_BASKET' : 70
    POSITION_LIMIT = {'AMETHYSTS' : 20, 'STARFRUIT' : 20, 'ORCHIDS': 100, 'CHOCOLATE': 250, 'STRAWBERRIES': 350, 'ROSES': 60, 'GIFT_BASKET': 60, 'COCONUT': 300, 'COCONUT_COUPON': 600}

    basket_std = 101.90140316248412 # best
    cont_buy_basket_unfill = 0
    cont_sell_basket_unfill = 0

    last_import = -1
    last_export = -1
    last_shipping = -1
    last_orchid_price = 0
    buy_orchids = False
    sell_orchids = False
    orchid_replay_size = 4
    humidity_cache = []
    sunlight_cache = []
    orchid_cache = []

    coconut_cache = []
    coconut_coupon_cache = []
    
    def compute_orders_regression(self, product, order_depth, acc_bid, acc_ask, LIMIT):
        orders: list[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        sell_vol, best_sell_pr = self.values_extract(osell)
        buy_vol, best_buy_pr = self.values_extract(obuy, 1)

        cpos = self.position[product]

        for ask, vol in osell.items():
            if ((ask <= acc_bid) or ((self.position[product]<0) and (ask == acc_bid+1))) and cpos < LIMIT:
                order_for = min(-vol, LIMIT - cpos)
                cpos += order_for
                assert(order_for >= 0)
                orders.append(Order(product, ask, order_for))

        undercut_buy = best_buy_pr + 1
        undercut_sell = best_sell_pr - 1

        bid_pr = min(undercut_buy, acc_bid) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, acc_ask)

        if cpos < LIMIT:
            num = LIMIT - cpos
            orders.append(Order(product, bid_pr, num))
            cpos += num
        
        cpos = self.position[product]
        

        for bid, vol in obuy.items():
            if ((bid >= acc_ask) or ((self.position[product]>0) and (bid+1 == acc_ask))) and cpos > -LIMIT:
                order_for = max(-vol, -LIMIT-cpos)
                # order_for is a negative number denoting how much we will sell
                cpos += order_for
                assert(order_for <= 0)
                orders.append(Order(product, bid, order_for))

        if cpos > -LIMIT:
            num = -LIMIT-cpos
            orders.append(Order(product, sell_pr, num))
            cpos += num

        return orders
    
    def compute_orders_regression_coconuts(self, product, order_depth, acc_bid, acc_ask, LIMIT):
        if (len(self.coconut_cache) < 4):
            return []
        
        orders: List[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        best_sell = next(iter(osell))
        best_buy = next(iter(obuy))

        mid_price = (best_sell + best_buy)/2
        
        next_price = self.predict_coconuts()
        print('acceptable price', next_price)
        product = "COCONUT"
        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            # mid_price = 
            if mid_price < next_price - 1: # int(best_ask) < next_price - 1:
                print("BUY", str(-best_ask_amount) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if mid_price > next_price + 1: # int(best_bid) > next_price + 1:
                print("SELL", str(best_bid_amount) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_amount))

        # osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        # obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        # sell_vol, best_sell_pr = self.values_extract(osell)
        # buy_vol, best_buy_pr = self.values_extract(obuy, 1)

        # cpos = self.position[product]

        # for ask, vol in osell.items():
        #     if not (((ask <= acc_bid) or ((self.position[product]<0) and (ask == acc_bid+1))) and cpos < LIMIT):
        #         order_for = min(-vol, LIMIT - cpos)
        #         cpos += order_for
        #         assert(order_for >= 0)
        #         orders.append(Order(product, ask, order_for))

        # undercut_buy = best_buy_pr + 1
        # undercut_sell = best_sell_pr - 1

        # bid_pr = min(undercut_buy, acc_bid) # we will shift this by 1 to beat this price
        # sell_pr = max(undercut_sell, acc_ask)

        # if not (cpos < LIMIT):
        #     num = LIMIT - cpos
        #     orders.append(Order(product, bid_pr, num))
        #     cpos += num
        
        # cpos = self.position[product]
        

        # for bid, vol in obuy.items():
        #     if not (((bid >= acc_ask) or ((self.position[product]>0) and (bid+1 == acc_ask))) and cpos > -LIMIT):
        #         order_for = max(-vol, -LIMIT-cpos)
        #         # order_for is a negative number denoting how much we will sell
        #         cpos += order_for
        #         assert(order_for <= 0)
        #         orders.append(Order(product, bid, order_for))

        # if not (cpos > -LIMIT):
        #     num = -LIMIT-cpos
        #     orders.append(Order(product, sell_pr, num))
        #     cpos += num

        return orders
    
    def values_extract(self, order_dict, buy=0):
        tot_vol = 0
        best_val = -1
        mxvol = -1

        for ask, vol in order_dict.items():
            if(buy==0):
                vol *= -1
            tot_vol += vol
            if tot_vol > mxvol:
                mxvol = vol
                best_val = ask
        
        return tot_vol, best_val
    
    def calc_next_price_starfruit(self):
        # bananas cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [-0.01869561,  0.0455032 ,  0.16316049,  0.8090892]
        intercept = 4.481696494462085
        nxt_price = intercept
        for i, val in enumerate(self.sf_cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))
    
    def compute_orders_amethyst(self, product, order_depth, acc_bid, acc_ask):
        orders: list[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        sell_vol, best_sell_pr = self.values_extract(osell)
        buy_vol, best_buy_pr = self.values_extract(obuy, 1)

        cpos = self.position[product]

        mx_with_buy = -1

        for ask, vol in osell.items():
            if ((ask < acc_bid) or ((self.position[product]<0) and (ask == acc_bid))) and cpos < self.POSITION_LIMIT['STARFRUIT']:
                mx_with_buy = max(mx_with_buy, ask)
                order_for = min(-vol, self.POSITION_LIMIT['STARFRUIT'] - cpos)
                cpos += order_for
                assert(order_for >= 0)
                orders.append(Order(product, ask, order_for))

        mprice_actual = (best_sell_pr + best_buy_pr)/2
        mprice_ours = (acc_bid+acc_ask)/2

        undercut_buy = best_buy_pr + 1
        undercut_sell = best_sell_pr - 1

        bid_pr = min(undercut_buy, acc_bid-1) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, acc_ask+1)

        if (cpos < self.POSITION_LIMIT['STARFRUIT']) and (self.position[product] < 0):
            num = min(40, self.POSITION_LIMIT['STARFRUIT'] - cpos)
            orders.append(Order(product, min(undercut_buy + 1, acc_bid-1), num))
            cpos += num

        if (cpos < self.POSITION_LIMIT['STARFRUIT']) and (self.position[product] > 15):
            num = min(40, self.POSITION_LIMIT['STARFRUIT'] - cpos)
            orders.append(Order(product, min(undercut_buy - 1, acc_bid-1), num))
            cpos += num

        if cpos < self.POSITION_LIMIT['STARFRUIT']:
            num = min(40, self.POSITION_LIMIT['STARFRUIT'] - cpos)
            orders.append(Order(product, bid_pr, num))
            cpos += num
        
        cpos = self.position[product]

        for bid, vol in obuy.items():
            if ((bid > acc_ask) or ((self.position[product]>0) and (bid == acc_ask))) and cpos > -self.POSITION_LIMIT['STARFRUIT']:
                order_for = max(-vol, -self.POSITION_LIMIT['STARFRUIT']-cpos)
                # order_for is a negative number denoting how much we will sell
                cpos += order_for
                assert(order_for <= 0)
                orders.append(Order(product, bid, order_for))

        if (cpos > -self.POSITION_LIMIT['STARFRUIT']) and (self.position[product] > 0):
            num = max(-40, -self.POSITION_LIMIT['STARFRUIT']-cpos)
            orders.append(Order(product, max(undercut_sell-1, acc_ask+1), num))
            cpos += num

        if (cpos > -self.POSITION_LIMIT['STARFRUIT']) and (self.position[product] < -15):
            num = max(-40, -self.POSITION_LIMIT['STARFRUIT']-cpos)
            orders.append(Order(product, max(undercut_sell+1, acc_ask+1), num))
            cpos += num

        if cpos > -self.POSITION_LIMIT['STARFRUIT']:
            num = max(-40, -self.POSITION_LIMIT['STARFRUIT']-cpos)
            orders.append(Order(product, sell_pr, num))
            cpos += num

        return orders
    
    def orchid_regression(self, sunlight, humidity):
        coefficients = [0.04013674419102109, 3.7792038307131612, 693.3200659097024]

        predicted_price = sunlight * coefficients[0] + humidity * coefficients[1] + coefficients[2]
        return int(round(predicted_price))
    
    def predict_with_replay_memory(self, orchid_price_replay_memory, sunlight_replay_memory, humidity_replay_memory):
        coefficients = [1.0032660592215041, -0.01661690483455555, 0.01774100307629441, -0.004772261712975734, -0.0067775624498480624, 0.013449829049283046, -0.010207885081724655, 0.00354740873126147, 0.4123593854358205, -1.0009058984766757, 0.7969951917929698, -0.2067842202425254, 0.25173645853783455]
        
        orchid_price_prediction = np.sum(orchid_price_replay_memory * coefficients[:self.orchid_replay_size]) + \
                                np.sum(sunlight_replay_memory * coefficients[self.orchid_replay_size:2*self.orchid_replay_size]) + \
                                np.sum(humidity_replay_memory * coefficients[2*self.orchid_replay_size:3*self.orchid_replay_size]) + \
                                coefficients[len(coefficients)-1]
        return orchid_price_prediction
    
    def compute_orders_orchids(self, order_depth, observations):
        orders = {'ORCHIDS' : []}
        prods = ['ORCHIDS']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}

        print(self.sunlight_cache)

        if len(self.sunlight_cache) == self.orchid_replay_size:
            self.sunlight_cache.pop(0)

        if len(self.humidity_cache) == self.orchid_replay_size:
            self.humidity_cache.pop(0)

        if len(self.orchid_cache) == self.orchid_replay_size:
            self.orchid_cache.pop(0)

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            print("actual price orchids:", mid_price[p])
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 

        # if sunlight_ma and humidity_ma and (observations.sunlight - sunlight_ma > 1 or observations.humidity - humidity_ma > 1):
        #     if self.last_import != -1 and (observations.importTariff - self.last_import > 0.2):
        #         self.buy_orchids = True

        #     if self.last_export != -1 and (observations.exportTariff - self.last_export > 0.2):
        #         self.buy_orchids = True

        #     if self.last_shipping != -1 and (observations.transportFees - self.last_shipping > 0.2):
        #         self.buy_orchids = True
        # elif sunlight_ma and humidity_ma and (observations.sunlight - sunlight_ma < -1 or observations.humidity - humidity_ma < -1):
        #     if self.last_import != -1 and (observations.importTariff - self.last_import < -0.2):
        #         self.sell_orchids = True

        #     if self.last_export != -1 and (observations.exportTariff - self.last_export < -0.2):
        #         self.sell_orchids = True

        #     if self.last_shipping != -1 and (observations.transportFees - self.last_shipping < -0.2):
        #         self.sell_orchids = True

        # if self.last_import != -1 and (observations.importTariff - self.last_import > 0.2):
        #     self.buy_orchids = True

        # if self.last_export != -1 and (observations.exportTariff - self.last_export > 1):
        #     self.buy_orchids = True

        # if self.last_shipping != -1 and (observations.transportFees - self.last_shipping > 0.1):
        #     self.buy_orchids = True

        # if self.last_import != -1 and (observations.importTariff - self.last_import < -0.2):
        #     self.sell_orchids = True

        # if self.last_export != -1 and (observations.exportTariff - self.last_export < -1):
        #     self.sell_orchids = True

        # if self.last_shipping != -1 and (observations.transportFees - self.last_shipping < -0.1):
        #     self.sell_orchids = True


        # if sunlight_ma and humidity_ma:
        #     print('sunlight buy signal:', observations.sunlight - sunlight_ma > 3)
        #     print('sunlight sell signal:', observations.sunlight - sunlight_ma < -3)
        #     print('humidity buy signal:', observations.humidity - humidity_ma > 3)
        #     print('humidity sell signal:', observations.humidity - humidity_ma < -3)
        # if sunlight_ma and humidity_ma and (observations.sunlight - sunlight_ma > 3 or observations.humidity - humidity_ma > 3):
        #     self.buy_orchids = True
        # elif sunlight_ma and humidity_ma and (observations.sunlight - sunlight_ma < -3 or observations.humidity - humidity_ma < -3):
        #     self.sell_orchids = True

        # if observations.sunlight < 3000 and observations.humidity < 70:
        #     self.sell_orchids = True
        # if observations.sunlight > 4000 and observations.humidity > 85:
        #     self.buy_orchids = True
        
        # if self.buy_orchids and self.position['ORCHIDS'] == self.POSITION_LIMIT['ORCHIDS']:
        #     self.buy_orchids = False
        # if self.sell_orchids and self.position['ORCHIDS'] == -self.POSITION_LIMIT['ORCHIDS']:
        #     self.sell_orchids = False


        


        if self.buy_orchids:
            vol = self.POSITION_LIMIT['ORCHIDS'] - self.position['ORCHIDS']
            orders['ORCHIDS'].append(Order('ORCHIDS', worst_sell['ORCHIDS'], vol))
        if self.sell_orchids:
            vol = self.position['ORCHIDS'] + self.POSITION_LIMIT['ORCHIDS']
            orders['ORCHIDS'].append(Order('ORCHIDS', worst_buy['ORCHIDS'], -vol))
        self.last_import = observations.importTariff
        self.last_export = observations.transportFees
        self.last_shipping = observations.humidity

        self.sunlight_cache.append(observations.sunlight)
        self.humidity_cache.append(observations.humidity)
        self.orchid_cache.append(mid_price['ORCHIDS'])

        self.last_orchid_price = mid_price['ORCHIDS']

        # print(';sajf;sakjfd', len(self.sunlight_cache) == self.orchid_replay_size and len(self.humidity_cache) == self.orchid_replay_size and len(self.orchid_cache) == self.orchid_replay_size)
        # if len(self.sunlight_cache) == self.orchid_replay_size and len(self.humidity_cache) == self.orchid_replay_size and len(self.orchid_cache) == self.orchid_replay_size:
        #     replay_memory = (self.orchid_cache, self.sunlight_cache, self.humidity_cache)
        #     prediction = self.predict_with_replay_memory(*replay_memory)

        #     orchid_lb = prediction-1
        #     orchid_ub = prediction+1
        #     acc_bid = {'ORCHIDS' : orchid_lb} # we want to buy at slightly below
        #     acc_ask = {'ORCHIDS' : orchid_ub} # we want to sell at slightly above

        #     # orders = self.compute_orders_orchids(state.order_depths, orchid_obs)
        #     orders['ORCHIDS'].append(self.compute_orders_regression('ORCHIDS', order_depth['ORCHIDS'], acc_bid['ORCHIDS'], acc_ask['ORCHIDS'], self.POSITION_LIMIT['ORCHIDS']))

        return orders
    
    def compute_orders_basket(self, order_depth):

        orders = {'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': [], 'GIFT_BASKET': []}
        prods = ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']
        osell, obuy, best_sell, best_buy, worst_sell, worst_buy, mid_price, vol_buy, vol_sell = {}, {}, {}, {}, {}, {}, {}, {}, {}

        for p in prods:
            osell[p] = collections.OrderedDict(sorted(order_depth[p].sell_orders.items()))
            obuy[p] = collections.OrderedDict(sorted(order_depth[p].buy_orders.items(), reverse=True))

            best_sell[p] = next(iter(osell[p]))
            best_buy[p] = next(iter(obuy[p]))

            worst_sell[p] = next(reversed(osell[p]))
            worst_buy[p] = next(reversed(obuy[p]))

            mid_price[p] = (best_sell[p] + best_buy[p])/2
            vol_buy[p], vol_sell[p] = 0, 0
            for price, vol in obuy[p].items():
                vol_buy[p] += vol 
                if vol_buy[p] >= self.POSITION_LIMIT[p]/10:
                    break
            for price, vol in osell[p].items():
                vol_sell[p] += -vol 
                if vol_sell[p] >= self.POSITION_LIMIT[p]/10:
                    break

        res_buy = mid_price['GIFT_BASKET'] - mid_price['CHOCOLATE']*4 - mid_price['STRAWBERRIES']*6 - mid_price['ROSES'] - 375
        res_sell = mid_price['GIFT_BASKET'] - mid_price['CHOCOLATE']*4 - mid_price['STRAWBERRIES']*6 - mid_price['ROSES'] - 375

        trade_at = self.basket_std*0.5
        close_at = self.basket_std*(-1000)

        pb_pos = self.position['GIFT_BASKET']
        pb_neg = self.position['GIFT_BASKET']

        uku_pos = self.position['ROSES']
        uku_neg = self.position['ROSES']


        basket_buy_sig = 0
        basket_sell_sig = 0

        if self.position['GIFT_BASKET'] == self.POSITION_LIMIT['GIFT_BASKET']:
            self.cont_buy_basket_unfill = 0
        if self.position['GIFT_BASKET'] == -self.POSITION_LIMIT['GIFT_BASKET']:
            self.cont_sell_basket_unfill = 0

        do_bask = 0

        if res_sell > trade_at:
            vol = self.position['GIFT_BASKET'] + self.POSITION_LIMIT['GIFT_BASKET']
            self.cont_buy_basket_unfill = 0 # no need to buy rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_sell_sig = 1
                orders['GIFT_BASKET'].append(Order('GIFT_BASKET', worst_buy['GIFT_BASKET'], -vol)) 
                self.cont_sell_basket_unfill += 2
                pb_neg -= vol
                #uku_pos += vol
        elif res_buy < -trade_at:
            vol = self.POSITION_LIMIT['GIFT_BASKET'] - self.position['GIFT_BASKET']
            self.cont_sell_basket_unfill = 0 # no need to sell rn
            assert(vol >= 0)
            if vol > 0:
                do_bask = 1
                basket_buy_sig = 1
                orders['GIFT_BASKET'].append(Order('GIFT_BASKET', worst_sell['GIFT_BASKET'], vol))
                self.cont_buy_basket_unfill += 2
                pb_pos += vol

        # if int(round(self.person_position['Olivia']['ROSES'])) > 0:

        #     val_ord = self.POSITION_LIMIT['UKULELE'] - uku_pos
        #     if val_ord > 0:
        #         orders['UKULELE'].append(Order('UKULELE', worst_sell['UKULELE'], val_ord))
        # if int(round(self.person_position['Olivia']['UKULELE'])) < 0:

        #     val_ord = -(self.POSITION_LIMIT['UKULELE'] + uku_neg)
        #     if val_ord < 0:
        #         orders['UKULELE'].append(Order('UKULELE', worst_buy['UKULELE'], val_ord))

        return orders
    
    def predict_coconuts(self):
        coefficients = [0.9624814518494764,
                        0.04900246016600207,
                        -0.00656214095442198,
                        -0.005184200768296066,
                        0.012032813103374451,
                        -0.0233345197230852,
                        0.012672593695095213,
                        -0.0009207580536969573,
                        2.3347427181706735]
        
        coconut_price_prediction = np.sum(np.array(self.coconut_cache) * coefficients[:self.orchid_replay_size]) + \
                                np.sum(np.array(self.coconut_coupon_cache) * coefficients[self.orchid_replay_size:2*self.orchid_replay_size]) + \
                                coefficients[len(coefficients)-1]
        return int(round(coconut_price_prediction))

    
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        # print("Observations: " + str(state.observations))

        result = {'AMETHYSTS' : [], 'STARFRUIT' : [], 'ORCHIDS': [], 'CHOCOLATE': [], 'STRAWBERRIES': [], 'ROSES': [], 'GIFT_BASKET': [], 'COCONUT': [], 'COCONUT_COUPON': []}

        for key, val in state.position.items():
            self.position[key] = val

        # if len(self.sf_cache) == self.starfruit_dim:
        #     self.sf_cache.pop(0)

        # _, bs_starfruit = self.values_extract(collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].sell_orders.items())))
        # _, bb_starfruit = self.values_extract(collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].buy_orders.items(), reverse=True)), 1)

        # self.sf_cache.append((bs_starfruit+bb_starfruit)/2)

        # print("this is the cache", self.sf_cache)

        # INF = 1e9
    
        # starfruit_lb = -INF
        # starfruit_ub = INF

        # if len(self.sf_cache) == self.starfruit_dim:
        #     starfruit_lb = self.calc_next_price_starfruit()-1
        #     starfruit_ub = self.calc_next_price_starfruit()+1

        # amethysts_lb = 10000
        # amethysts_ub = 10000

        # acc_bid = {'AMETHYSTS' : amethysts_lb, 'STARFRUIT' : starfruit_lb} # we want to buy at slightly below
        # acc_ask = {'AMETHYSTS' : amethysts_ub, 'STARFRUIT' : starfruit_ub} # we want to sell at slightly above

        # for product in state.order_depths:
        #     order_depth: OrderDepth = state.order_depths[product]
        #     orders: List[Order] = []
            
        #     # print("Acceptable price : " + str(acceptable_price))
        #     print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
        #     if (product == 'AMETHYSTS'):
        #       order_depth: OrderDepth = state.order_depths[product]
        #       orders = self.compute_orders_amethyst(product, order_depth, acc_bid[product], acc_ask[product])
        #       result[product] += orders

        #     if (product == 'STARFRUIT'):
        #         order_depth: OrderDepth = state.order_depths[product]
        #         orders = self.compute_orders_regression(product, order_depth, acc_bid[product], acc_ask[product], self.POSITION_LIMIT[product])
        #         result[product] += orders
            
        #     result[product] = orders
        #     print("these are the orders", orders)
    
		    # String value holding Trader state data required. 
			# 	It will be delivered as TradingState.traderData on next execution.
    
        # orders = self.compute_orders_basket(state.order_depths)
        # result['GIFT_BASKET'] += orders['GIFT_BASKET']
        # result['CHOCOLATE'] += orders['CHOCOLATE']
        # result['STRAWBERRIES'] += orders['STRAWBERRIES']
        # result['ROSES'] += orders['ROSES']


        # orchid_obs = state.observations.conversionObservations['ORCHIDS']
        # orders = self.compute_orders_orchids(state.order_depths, orchid_obs)
        # # result['ORCHIDS'] += orders['ORCHIDS']
        # # print('OBSERVATIONS', orchid_obs.sunlight, orchid_obs.humidity)
        
        # print('sunlight:', len(self.sunlight_cache), 'humidity:', len(self.humidity_cache), 'orchid:', len(self.orchid_cache))
        # print('regression', len(self.sunlight_cache) == self.orchid_replay_size and len(self.humidity_cache) == self.orchid_replay_size and len(self.orchid_cache) == self.orchid_replay_size)
        # if len(self.sunlight_cache) == self.orchid_replay_size and len(self.humidity_cache) == self.orchid_replay_size and len(self.orchid_cache) == self.orchid_replay_size:
        #     replay_memory = (self.orchid_cache, self.sunlight_cache, self.humidity_cache)
        #     replay_memory = tuple(np.array(x) for x in list(replay_memory))
        #     orchid_lb = self.predict_with_replay_memory(*replay_memory)-1
        #     orchid_ub = self.predict_with_replay_memory(*replay_memory)+1
        #     acc_bid = {'ORCHIDS' : orchid_lb} # we want to buy at slightly below
        #     acc_ask = {'ORCHIDS' : orchid_ub} # we want to sell at slightly above
        #     print('price prediction:', self.predict_with_replay_memory(*replay_memory))

        #     orders = self.compute_orders_regression('ORCHIDS', state.order_depths['ORCHIDS'], acc_bid['ORCHIDS'], acc_ask['ORCHIDS'], self.POSITION_LIMIT['ORCHIDS'])
        #     result['ORCHIDS'] += orders





        if len(self.coconut_cache) == self.orchid_replay_size:
            self.coconut_cache.pop(0)

        if len(self.coconut_coupon_cache) == self.orchid_replay_size:
            self.coconut_coupon_cache.pop(0)

        _, bs_coconut = self.values_extract(collections.OrderedDict(sorted(state.order_depths['COCONUT'].sell_orders.items())))
        _, bb_coconut = self.values_extract(collections.OrderedDict(sorted(state.order_depths['COCONUT'].buy_orders.items(), reverse=True)), 1)
        _, bs_coconut_coupon = self.values_extract(collections.OrderedDict(sorted(state.order_depths['COCONUT_COUPON'].sell_orders.items())))
        _, bb_coconut_coupon = self.values_extract(collections.OrderedDict(sorted(state.order_depths['COCONUT_COUPON'].buy_orders.items(), reverse=True)), 1)

        self.coconut_cache.append((bs_coconut+bb_coconut)/2)
        self.coconut_coupon_cache.append((bs_coconut_coupon+bb_coconut_coupon)/2)

        print("this is the cache", self.coconut_cache)

        INF = 1e9
    
        coconut_lb = -INF
        coconut_ub = INF
        coconut_cache_lb = -INF
        coconut_cache_ub = INF

        # print('coconut prediction:', self.predict_coconuts(), "coconut actual:", (bs_coconut+bb_coconut)/2)
        if len(self.coconut_cache) == self.orchid_replay_size:
            coconut_lb = self.predict_coconuts()-4
            coconut_ub = self.predict_coconuts()+4
        if len(self.coconut_coupon_cache) == self.orchid_replay_size:
            coconut_cache_lb = self.calc_next_price_starfruit()-1
            coconut_cache_ub = self.calc_next_price_starfruit()+1

        acc_bid = {'COCONUT' : coconut_lb} # we want to buy at slightly below
        acc_ask = {'COCONUT' : coconut_ub} # we want to sell at slightly above

        order_depth: OrderDepth = state.order_depths['COCONUT']
        orders: List[Order] = []

        order_depth: OrderDepth = state.order_depths['COCONUT']
        orders = self.compute_orders_regression_coconuts('COCONUT', order_depth, acc_bid['COCONUT'], acc_ask['COCONUT'], self.POSITION_LIMIT['COCONUT'])        
        result['COCONUT'] = orders
        print("these are the orders", orders)

        traderData = "DATA"
        
        # Sample conversion request. Check more details below.
        conversions = 1
        return result, conversions, traderData