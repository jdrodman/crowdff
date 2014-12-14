#This is the quality module, it prodives a method for computing the accuracy of a user or projected roster for a given team in a given week.  It is called and stored from within the aggregation module

def get_lineup_accuracy(lineup, optimal_lineup):
    lineup_set = set()
    o_lineup_set = set()
    for position in lineup: 
        lineup_set |= set(lineup[position])
        o_lineup_set |= set(optimal_lineup[position])
    N = float(len(lineup_set & o_lineup_set))
    D = float(len(o_lineup_set))
    return (N, D)
    
    
    