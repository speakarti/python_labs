# characters = ["Krillin","Goku", "Goku", "Gohan", "Piccolo", "Krillin","Goku", "Vegeta", "Gohan", "Piccolo", "Piccolo","Goku", "Vegeta", "Goku", "Piccolo"]
# character_map = {character:[] for character in set(characters)}
# print(character_map)
# Use enumerate to store the index for each occurence
# for index, character in enumerate(characters):
#     character_map[character].append(index)

# character_map

characters = ["Krillin","Goku", "Goku", "Gohan", "Piccolo", "Krillin","Goku", "Vegeta", "Gohan", "Piccolo", "Piccolo","Goku", "Vegeta", "Goku", "Piccolo"]
my_dict = {}
for index,value in enumerate(characters):
    print(index, value)
    #my_dict(value) = 
