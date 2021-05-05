class artifacts:
    def __init__(self):
        # 2-digit language code
        self.id = 'en'
        # 3-digit language code
        self.code = 'eng'
        # Unicode flag
        self.flags = ['ðŸ‡ºðŸ‡¸']
        
        self.types = ['Flower', 'Plume', 'Sands', 'Goblet', 'Circlet']
            
        self.sets = ['Adventurer',
            'Lucky Dog',
            'Traveling Doctor',
            'Prayers for Wisdom',
            'Prayers to Springtime',
            'Prayers for Illumination',
            'Prayers for Destiny',
            'Instructor',
            'Berserker',
            'The Exile',
            'Resolution of Sojourner',
            'Martial Artist',
            'Defender\'s Will',
            'Tiny Miracle',
            'Brave Heart',
            'Gambler',
            'Scholar',
            'Gladiator\'s Finale',
            'Maiden Beloved',
            'Noblesse Oblige',
            'Bloodstained Chivalry',
            'Wanderer\'s Troupe',
            'Viridescent Venerer',
            'Thundering Fury',
            'Thundersoother',
            'Crimson Witch of Flames',
            'Lavawalker',
            'Archaic Petra',
            'Retracing Bolide',
            'Heart of Depth',
            'Blizzard Strayer',
            'Tenacity of the Millelith',
            'Pale Flame'
            ]
            
        # Get index through reverse dictionary
        # 1 full iteration followed by 100 fast lookups
        # is better than to do 100 half-iterations
        self.types_dict = dict(zip(self.types,range(0,len(self.types))))
        self.sets_dict = dict(zip(self.sets,range(0,len(self.sets))))
            
        self.all = self.types + self.sets
      
class en(artifacts):
	pass
    
class idn(artifacts):
    # Placeholder
	pass
        
# Class for an artifact piece
class piece:
    def __init__(self, type, level, set, stats, lang=en()):
        self.type = lang.types_dict[type]   # Store as index
        self.level = level
        self.set = lang.sets_dict[set]      # Store as index
        self.stats = stats
        
        self.score = (0,0)
        self.main = (0,0)
        self.sub = (0,0)
        
    def get_type(self, lang=en()):
        return lang.types[self.type]
        
    def get_set(self, lang=en()):
        return lang.sets[self.set]
        
    def set_score(self, score, main, sub):
        self.score = score
        self.main = main
        self.sub = sub
    
    def get_array(self, lang=en()):
        # Flatten everything into an array, the dynamic stats is in the end.
        return [lang.types[self.type], self.level, lang.sets[self.set]] + \
            list(self.score) + list(self.main) + list(self.sub) + \
            [item for sublist in self.stats for item in sublist]
        
    def print(self, lang=en()):
        print(f"+{self.level} {lang.types[self.type]}")
        [print(f" - {x[0]} {x[1]}") for x in self.stats]
        print(lang.sets[self.set])
        print(f"Total: {self.score[0]:.2f} ({self.score[1]:.2f}%) \n" +
            f"  Main: {self.main[0]:.2f} ({self.main[1]:.2f}%) \n" +
            f"  Sub: {self.sub[0]:.2f} ({self.sub[1]:.2f}%) \n")
