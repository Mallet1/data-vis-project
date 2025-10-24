from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import collections
from collections import defaultdict
import json
import copy

empty_dict = {'AMETHYSTS' : 0, 'STARFRUIT' : 0}

class Trader:
    sf_cache = []
    starfruit_dim = 4
    position = copy.deepcopy(empty_dict)
    POSITION_LIMIT = {'AMETHYSTS' : 20, 'STARFRUIT' : 20}
    
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
    
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        for key, val in state.position.items():
            self.position[key] = val

        if len(self.sf_cache) == self.starfruit_dim:
            self.sf_cache.pop(0)

        _, bs_starfruit = self.values_extract(collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].sell_orders.items())))
        _, bb_starfruit = self.values_extract(collections.OrderedDict(sorted(state.order_depths['STARFRUIT'].buy_orders.items(), reverse=True)), 1)

        self.sf_cache.append((bs_starfruit+bb_starfruit)/2)

        print("this is the cache", self.sf_cache)

        INF = 1e9
    
        starfruit_lb = -INF
        starfruit_ub = INF

        if len(self.sf_cache) == self.starfruit_dim:
            starfruit_lb = self.calc_next_price_starfruit()-1
            starfruit_ub = self.calc_next_price_starfruit()+1

        amethysts_lb = 10000
        amethysts_ub = 10000

        acc_bid = {'AMETHYSTS' : amethysts_lb, 'STARFRUIT' : starfruit_lb} # we want to buy at slightly below
        acc_ask = {'AMETHYSTS' : amethysts_ub, 'STARFRUIT' : starfruit_ub} # we want to sell at slightly above


				# Orders to be placed on exchange matching engine
        result = {'AMETHYSTS' : [], 'STARFRUIT' : []}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            
            # print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if (product == 'AMETHYSTS'):
              order_depth: OrderDepth = state.order_depths[product]
              orders = self.compute_orders_amethyst(product, order_depth, acc_bid[product], acc_ask[product])
              result[product] += orders

              # acceptable_price = 10000  # Participant should calculate this value
              # if len(order_depth.sell_orders) != 0:
              #     best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
              #     if int(best_ask) < acceptable_price:
              #         print("BUY", str(-best_ask_amount) + "x", best_ask)
              #         orders.append(Order(product, best_ask, -best_ask_amount))
      
              # if len(order_depth.buy_orders) != 0:
              #     best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
              #     if int(best_bid) > acceptable_price:
              #         print("SELL", str(best_bid_amount) + "x", best_bid)
              #         orders.append(Order(product, best_bid, -best_bid_amount))

            if (product == 'STARFRUIT'):
                order_depth: OrderDepth = state.order_depths[product]
                orders = self.compute_orders_regression(product, order_depth, acc_bid[product], acc_ask[product], self.POSITION_LIMIT[product])
                result[product] += orders

                # acceptable_price = 5048  # Participant should calculate this value
                # buffer = 10 # current best: 10

                # if len(order_depth.sell_orders) != 0:
                #   best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                #   if int(best_ask) < acceptable_price-buffer:
                #       print("BUY", str(-best_ask_amount) + "x", best_ask)
                #       orders.append(Order(product, best_ask, -best_ask_amount))
      
                # if len(order_depth.buy_orders) != 0:
                #   best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                #   if int(best_bid) > acceptable_price+buffer:
                #       print("SELL", str(best_bid_amount) + "x", best_bid)
                #       orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
            print("these are the orders", orders)
    
		    # String value holding Trader state data required. 
				# It will be delivered as TradingState.traderData on next execution.

        traderData = "DATA"
        
				# Sample conversion request. Check more details below. 
        conversions = 1
        return result, conversions, traderData