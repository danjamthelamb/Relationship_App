import random as r
import easygui
from texter_log import friends_d
from texter_log import family_d
from texter_log import prev_d


def CheckTotals(dic):
    total = 0
    dic_len = len(dic)
    for i in dic:
        key = i
        val = dic[i]
        total += val
    if total < dic_len:
        return False
    else:
        for i in dic:
            key = i
            val = dic[i] 
            update = {key : 0}
            dic.update(update)
        return True
            
def GetUncontacted(dic):
    uncontacted_ppl = []
    for i in dic:
        key = i
        val = dic[i]
        if val == 0:
            uncontacted_ppl.append(key)
    return uncontacted_ppl


# Identify Uncontacted People, Reset Dictionaries if needed.
fam_check = CheckTotals(family_d)
if not fam_check:
    print ('Not every family member has been contacted yet.')
else:
    print ('Every family member has been contacted. Resetting Dictionary')
        
frnd_check = CheckTotals(friends_d)
if not frnd_check:
    print ('Not every friend has been contacted yet.')
else:
    print ('Every friend has been contacted. Resetting Dictionary')

    
# Family
uncontacted_fam = GetUncontacted(family_d)
        
# Friends
uncontacted_frnd = GetUncontacted(friends_d)


# Establish Previous People
prev_f = prev_d['friend']
prev_r = prev_d['relative']


# Randomly Select People
trapped = True

while trapped:
    rand_friend_num = r.randrange(len(uncontacted_frnd))-1 # Chooses a random friend
    rand_fam_num = r.randrange(len(uncontacted_fam))-1 # Chooses a random family member
    friend_name = uncontacted_frnd[rand_friend_num] # Name of the chosen friend
    fam_name = uncontacted_fam[rand_fam_num] # name of the chosen friend
    if friend_name == prev_f or fam_name == prev_r:
        print ('Error: Repeated selection. Drawing new names.')
        print (f'•••• Previous Friend: {prev_f}.')
        print (f'•••• •••• Selected Friend: {friend_name}.')
        print (f'\n•••• Previous Relative: {prev_r}.')
        print (f'•••• •••• Selected Friend: {fam_name}.')
    else:
        break
    

# Create Update Contact Dictionary
fam_chosen_index = family_d[fam_name] # Gets the value for the chosen fam member
frnd_chosen_index = friends_d[friend_name] # Gets the value for the chosen friend
fam_update = {fam_name : 1} # Creates update for chosen family mem
friend_update = {friend_name : 1} # Create update chosen friend
prev_update = {'friend' : friend_name, 'relative' : fam_name}
print (f'Updating status for {friend_name} in friend dictionary.')
print (f'Updating status for {fam_name} in relative dictionary.')


# Update Contact Dictionary
family_d.update(fam_update)
friends_d.update(friend_update)
prev_d.update(prev_update)

# Update Contact Dictionary
family_d.update(fam_update)
friends_d.update(friend_update)


# Update the file log
with open('texter_log.py','r+') as myfile:
    data = myfile.read()
    myfile.seek(0)
    myfile.write(f'family_d = {family_d}\nfriends_d = {friends_d}\nprev_d = {prev_d}')
    myfile.truncate()
    myfile.close()

    
easygui.msgbox(f"Text the following people:\nFriend - {friend_name}\nRelative - {fam_name}", title="Relationship App")