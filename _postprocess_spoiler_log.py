import os

char_names = ["TERRA", "LOCKE", "CYAN", "SHADOW", "EDGAR", "SABIN", "CELES", "STRAGO", "RELM", "SETZER", "MOG", "GAU", "GOGO", "UMARO"]

esper_names = ["Ramuh", "Ifrit", "Shiva", "Siren", "Terrato", "Shoat", "Maduin", "Bismark", "Stray", "Palidor",
               "Tritoch", "Odin", "Raiden", "Bahamut", "Alexandr", "Crusader", "Ragnarok", "Kirin", "ZoneSeek",
               "Carbunkl", "Phantom", "Sraphim", "Golem", "Unicorn", "Fenrir", "Starlet", "Phoenix"]

flagstr = "-cg -sl -oa 2.1.1.2.4.4 -ob 3.1.1.4.4.4 -sc1 umaro -sc2 mog -sc3 terra -sal -eu -csrp 90 135 -fst -brl -slr 1 5 -lmprp 75 125 -lel -srr 30 40 -rnl -rnc -sdr 8 8 -das -dda -dns -sch -com 16999999999999999999199999 -rec1 28 -rec2 23 -rec3 13 -rec4 5 -rec5 6 -xpm 3 -mpm 5 -gpm 5 -nxppd -lsced 1.5 -hmced 1.5 -xgced 2 -ase 2 -msl 40 -sed -sfb -bbs -be -bnu -res -fer 0 -escr 100 -dgne -wnz -mmnu -cmd -esr 1 5 -ebr 100 -emprp 75 75 -ems -nm1 random -rnl1 -rns1 -nm2 random -rnl2 -rns2 -nmmi -gp 5000 -smc 3 -sws 2 -sfd 2 -ieor 66 -ieror 100 -csb 1 32 -mca -stra -saw -sisr 100 -sprp 25 75 -sdm 5 -npi -snbr -snil -ccsr 50 -cms -cor -crr -crvr 115 199 -crm -ari -anca -adeh -nfps -nu -fs -fe -fvd -fr -fj -fbs -fedc -as -ond -rr -yreflect -frw -dru -drun"

fn = 'FFIII_out.txt'
events = ['Whelk', 'Lone Wolf', 'Narshe Battle', 'Tritoch', "Umaro's Cave"]
goal = ['esper', 'esper', 'esper', 'esper', 'character']

flag = True
ctr = 0
while flag:
    ctr += 1
    print('Take',ctr,'...')

    result = ['' for i in range(len(goal))]

    # run WC:
    os.system('wc.py -i FFIII.smc -o FFIII_out.smc ' + flagstr)

    # read spoiler log
    f = open(fn)
    nl = f.readline()
    while nl.find('Events') == -1:
        nl = f.readline()

    # parse events
    nl = f.readline()
    reward = []
    output = []
    while nl.find('----') == -1:
        for e in events:
            if nl[:len(e)] == e:
                this_reward = nl.split('  ')[-1][:-1].lstrip(' ')
                if this_reward.find(','):
                    this_reward = this_reward.split(',')[0]
                if this_reward in char_names:
                    result[events.index(e)] = 'character'
                    output.append([e, this_reward])
                elif this_reward in esper_names:
                    result[events.index(e)] = 'esper'
                    output.append([e, this_reward])

        nl = f.readline()

    if result == goal:
        print('\n',result,'\n',output)
        flag = False

print('Found a contender!')
for o in output:
    print(o[0], '-->', o[1])