import string,cgi,time, json, random, copy, os, copy, urllib, go, urllib2, time, config, threading, multiprocessing
import pybitcointools as pt
import state_library
genesis={'zack':'zack', 'length':-1, 'nonce':'22', 'sha':'00000000000'}
genesisbitcoin=291881-1170#1220
#If you are the first person to start mining this currency, you should probably change 290917 to whatever the current bitcoin block count it.
chain=[genesis]
chain_db='chain.db'
transactions_database='transactions.db'

#I call my database appendDB because this type of database is very fast to append data to.
def line2dic(line):
    return json.loads(line.strip('\n'))
def load_appendDB(file):
    out=[]
    try:
        with open(file, 'rb') as myfile:
            a=myfile.readlines()
            for i in a:
                if i.__contains__('"'):
                    out.append(line2dic(i))
    except:
        pass
    return out
def ex(db_extention, db):
    return db.replace('.db', db_extention+'.db')
def load_transactions(db_extention=""):
    return load_appendDB(ex(db_extention, transactions_database))
def load_chain(db_extention=''):
    open(ex(db_extention, chain_db), 'a').close()
    current=load_appendDB(ex(db_extention, chain_db))
    if len(current)<1:
        return [genesis]
    if current[0]!=genesis:
        current=[genesis]+current
    return current
def reset_appendDB(file):
    open(file, 'w').close()
def reset_transactions(db_ex=''):
    return reset_appendDB(ex(db_ex, transactions_database))
def reset_chain(db_ex=''):
    return reset_appendDB(ex(db_ex, chain_db))
def push_appendDB(file, tx):
    with open(file, 'a') as myfile:
        myfile.write(json.dumps(tx)+'\n')
def add_transactions(txs, db_ex=''):#to local pool
    #This function is order txs**2, that is risky
    txs_orig=copy.deepcopy(txs)
    count=0
    #    print('txs: ' +str(txs_orig))
    def f(x):
        if '' in x:
            return 
    if 'error' in txs:
        return
    for tx in sorted(txs_orig, key=lambda x: x['count']):
        if add_transaction(tx, db_ex):
            count+=1
            txs.remove(tx)
    if count>0:
        add_transactions(txs, db_ex)
def add_transaction(tx, db_ex=''):#to local pool
    if tx['type']=='mint':
        return False
    transactions=load_transactions(db_ex)
    state=state_library.current_state(db_ex)
    if verify_transactions(transactions+[tx], state)['bool']:
        push_appendDB(ex(db_ex, transactions_database), tx)
        return True
    return False
def chain_push(block, db_extention=''):
    statee=state_library.current_state(db_extention)    
    print('CHAIN PUSH')
    if new_block_check(block, statee):
#        print('PASSED TESTS')
        state=verify_transactions(block['transactions'], statee)
        state=state['newstate']
        state['length']+=1
        state['recent_hash']=block['sha']
        state_library.save_state(state, db_extention)
        if block['length']%10==0 and block['length']>11:
            state_library.backup_state(state, db_extention)
        txs=load_transactions(db_extention)
        reset_transactions(db_extention)
        add_transactions(txs, db_extention)
#        print('exiting Chain Push')
        return push_appendDB(ex(db_extention, chain_db), block)
    else:
        print('FAILED TESTS')
        return 'bad'
def shorten_chain_db(new_length, db_ex=''):
    f=open(ex(db_ex, chain_db), 'r')
    lines = f.readlines()
    f.close()
    f = open(ex(db_ex, chain_db),"w")
    i=0
    for line in lines:
        a=line2dic(line)
        if a['length']<new_length:# and a['length']>new_length-1500:
            f.write(line)
    f.close()
def chain_unpush(db_ex=''):
    chain=load_chain(db_ex)
    orphaned_txs=[]
    txs=load_transactions(db_ex)
    state=state_library.current_state(db_ex)
    length=state['length']
    state=state_library.recent_backup(db_ex)
    for i in range(length-state['length']):
        try:
            orphaned_txs+=chain[-1-i]['transactions']
        except:
            pass
    shorten_chain_db(state['length'], db_ex)
    state_library.save_state(state, db_ex)
    reset_transactions(db_ex)
    add_transactions(orphaned_txs, db_ex)
    add_transactions(txs, db_ex)
count_value=0
count_timer=time.time()-60
def probability(p, func):
    if random.random()<p:
        return func
def getblockcount():
    global count_value
    global count_timer
    if time.time()-count_timer<60:
        return count_value
    try:
        peer='http://blockexplorer.com/q/getblockcount'
        URL=urllib.urlopen(peer)
        URL=URL.read()
        count_value=int(URL)
    except:
        peer='http://blockchain.info/q/getblockcount'
        URL=urllib.urlopen(peer)
        URL=URL.read()
        count_value=int(URL)
    count_timer=time.time()
    return count_value
hash_dic={}
def getblockhash(count):
    global hash_dic
    if str(count) in hash_dic:
        return hash_dic[str(count)]
    try:
        peer='http://blockexplorer.com/q/getblockhash/'+str(count)
        URL=urllib.urlopen(peer)
        URL=URL.read()
        int(URL, 16)
        hash_dic[str(count)]=URL
        return URL
    except:
        peer='http://blockchain.info/q/getblockhash/'+str(count)
        URL=urllib.urlopen(peer)
        URL=URL.read()
        int(URL, 16)
        hash_dic[str(count)]=URL
        return URL

def package(dic):
    return json.dumps(dic).encode('hex')
def unpackage(dic):
    try:
        return json.loads(dic.decode('hex'))
    except:
        error('here')
def difficulty(leng):
    def buffer(s, n):
        while len(s)<n:
            s='0'+s
        return s
    '''
    try:
        hashes_required=int((10**60)*((9.0/10)**(float(bitcoin_count)-float(genesisbitcoin)-(float(leng)/10)))+1)#for bitcoin
#    hashes_required=int((10**60)*((9.0/10)**(float(bitcoin_count)-float(genesisbitcoin)-(float(leng)/2.5)))+1)#for litcoin
#    hashes_required=int((10**60)*((9.0/10)**(float(bitcoin_count)-float(genesisbitcoin)-(float(leng)/25)))+1)#for laziness, every 6 seconds??
    except:
        hashes_required=999999999999999999999999999999999999999999999999999999999999
    '''
    hashes_required=3000000
    out=buffer(hex(int('f'*64, 16)/hashes_required)[2:], 64)
    return out
def blockhash(chain_length, nonce, state, transactions):
    fixed_transactions=[]
    if len(transactions)==0:
        error('here')
    for i in transactions:
        new=''
        for key in sorted(i.keys()):
            new=new+str(key)+':'+str(i[key])+','
        fixed_transactions.append(new)
    exact=str(chain_length)+str(nonce)+str(state['recent_hash'])+str(sorted(fixed_transactions))
#    return {'hash':pt.sha256(exact), 'exact':exact}
    return {'hash':pt.sha256(exact)}
def reverse(l):
    out=[]
    while l != []:
        out=[l[0]]+out
        l=l[1:]
    return out
def new_block_check(block, state):
    def f(x):
        return str(block[x])
    if 'length' not in block or 'transactions' not in block:
        print('ERRROR !')
        return False
    diff=difficulty(f('length'))
    ver=verify_transactions(block['transactions'], state)
    if not ver['bool']:
        print('44')
        return False
#    print('new_ block: ' +str(block))
    if f('sha') != blockhash(f('length'), f('nonce'), state, block['transactions'])['hash']:
        print('blockhash: ' +str(blockhash(f('length'), f('nonce'), state, block['transactions'])))
        print('sha: ' +str(f('sha')))
        print('block invalid because blockhash was computed incorrectly')
#        error('here')
        return False
#    a=getblockcount()
#    '''
#    if int(f('bitcoin_count'))>int(a):
#        print('website: ' + str(type(a)))
#        print('f: ' +str(type(f('bitcoin_count'))))
#        print('COUNT ERROR')
#        return False
#    '''
    elif f('sha')>diff:
        print('block invalid because blockhash is not of sufficient difficulty')
        return False
#    '''
#    elif f('bitcoin_hash')!=getblockhash(int(f('bitcoin_count'))):
#        print('bitcoin _hash: ' +f('bitcoin_hash'))
#        print('bitcoin_count: ' +f('bitcoin_count'))
#        print('blockhash: ' +str(getblockhash(int(f('bitcoin_count')))))
#        print('block invalid because it does not contain the correct bitcoin hash')
#        error('here')
#        return False
#    '''
    elif f('prev_sha')!=state['recent_hash']:
        print('block invalid because it does not contain the previous block\'s hash')
        return False
    return True

def verify_transactions(txs, state):
    txs=copy.deepcopy(txs)
    if len(txs)==0:
        return {'bool':True, 'newstate':state}
#    print('txs: ' +str(txs))
    length=len(txs)
    state=copy.deepcopy(state)
    remove_list=[]
    for i in txs:#maybe this should be sorted
        (state, booll) = go.attempt_absorb(i, state)
        if booll:
            remove_list.append(i)
    for i in remove_list:
        txs.remove(i)
    if len(txs)>=length:
        print('HERE')
#        print(txs)
        return {'bool':False}
    if len(txs)==0:
        return {'bool':True, 'newstate':state}
    else:
        return verify_transactions(txs, state)
def send_command(peer, command):
    if False:#command['type'] in ['pushtx', 'pushblock']:
        t=threading.Thread(target=send_command_1, args=(peer, command))
        t.start()
    else:
        return send_command_1(peer, command)

def send_command_1(peer, command):
#    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    command['version']=4
    url=peer.format(package(command))
    print('in send command')
    time.sleep(1)#so we don't DDOS the networking computers which we all depend on.
    if 'onion' in url:
        try:
            print('trying privoxy method')
            proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
            opener = urllib2.build_opener(proxy_support) 
            out=opener.open(url)
            out=out.read()
            print('privoxy succeeded')
        except:
            print('url: ' +str(url))
            out={'error':'cannot connect to peer'}
    else:
        try:
            print('attempt to open: ' +str(url))
            URL=urllib.urlopen(url)
            out=URL.read()
        except:
            print('url: ' +str(url))
            out={'error':'cannot connect to peer'}
    try:
        return unpackage(out)
    except:
        return out

def easy_threading(f, lis):
    pool = multiprocessing.Pool()
    n = multiprocessing.cpu_count()
    out=[]
    for i in xrange(n):
        print('f: ' +str(f))
        print('lis: ' +str(lis))
        #(260, '00037ec8ec25e6d2c0bafefd59ebbd0b471449f24ac401db5abd74229ff6635L', 0, {u'04b568858a407a8721923b89df9963d30013639ac690cce5f555529b77b83cbfc76950f90be717e38a3ece1f5558f40179f8c9502deca11183bb3a3aea797736a6': {'count': 31, 'amount': 3000000}, 'length': 260, u'047a4a994d2648e15812288643c6266cf33a0823ea8e71bc4cbd13aeb53b761aed0c683d30f757784bfdbe59a4d98886ddf1e7a2aa6295a74aa1175ff556b35c2b': {'count': 231, 'amount': 23000000}, 'recent_hash': u'0001a6c47fd718ca6de35bd45fb99820f628f5012646027f948df4be2c80f2f6'}, [{'count': 31, 'amount': 100000, 'type': 'mint', 'id': '04b568858a407a8721923b89df9963d30013639ac690cce5f555529b77b83cbfc76950f90be717e38a3ece1f5558f40179f8c9502deca11183bb3a3aea797736a6'}])
        a=pool.apply(f, lis)
        out.append(a)
    print('out: ' +str(out))
    pool.close()
    pool.join()
    return out

def mine_2(length, diff, nonce, state, transactions):
    print('in mine 2')
    t=time.time()
    for i in range(config.hashes_till_check):
        nonce=random.randint(0,10000000000000000)
        sha=blockhash(length, nonce, state, transactions)
#        print('type diff: ' +str(diff))
#        print('type sha: ' +str(sha['hash']))
        if diff>=sha['hash']:
            block={'nonce':nonce, 'length':length, 
                   'sha':sha['hash'], 
                   'transactions':transactions, 
                   'prev_sha':state['recent_hash']}
            #            print('new link####################: ' +str(block))
            print('a: ' +str(block))
            return block
            #            return block
    print('was unable to find block in '+str(time.time()-t)+' seconds.')
    return False
def mine_1(reward_pubkey, peers, times, db_extention):
#    bitcoin_count=getblockcount()
    state=state_library.current_state(db_extention)
    diff=difficulty(state['length']+1)
    sha={'hash':'f'*64}
    print('start mining ' +str(times)+ ' times')
#    bitcoin_hash=getblockhash(bitcoin_count)
    transactions=load_transactions(db_extention)
    extra=0
    for tx in transactions:
        if tx['id']==reward_pubkey:
            extra+=1
    if reward_pubkey not in state:
        state[reward_pubkey]={'count':1, 'amount':0}
    if 'count' not in state[reward_pubkey]:
        state[reward_pubkey]['count']=1
    count=state[reward_pubkey]['count']+extra
    transactions.append({'type':'mint', 'amount':10**5, 'id':reward_pubkey, 'count':count})
    length=state['length']
    nonce=0
    hash_count=0
#    blocks=easy_threading(mine_2, (length, diff, nonce, state, transactions))
    blocks=[mine_2(length, diff, nonce, state, transactions)]
    print('blocks:' + str(blocks))
    blocks=filter(lambda x: x!=False, blocks)
    if len(blocks)>0:
        print('blocks:' + str(blocks))
        for block in blocks:
            chain_push(block)
        #    pushblock(block, peers)

def mainloop(reward_pubkey, peers, hashes_till_check, db_extention=''):
    while True:
        peer_check_all(peers, db_extention)
        if hashes_till_check>0:
            mine_1(reward_pubkey, peers, hashes_till_check, db_extention)
        if db_extention=='':
            a=load_appendDB('suggested_transactions.db')
            add_transactions(a)
            reset_appendDB('suggested_transactions.db')
            a=load_appendDB('suggested_blocks.db')
            #            for block in a:
            #                chain_push(block)
#            print('a: ' + str(a))
            if len(a)>0:
                chain_push(a[0])
            reset_appendDB('suggested_blocks.db')
        else:
            peer_check_all(peers, db_extention)
            time.sleep(2)
            
def fork_check(newblocks, state):#while we are mining on a forked chain, this check returns True. once we are back onto main chain, it returns false.
    try:
#        hashes=filter(lambda x: 'prev_sha' in x and x['prev_sha']==state['recent_hash'], newblocks)
        hashes=filter(lambda x: 'sha' in x and x['sha']==state['recent_hash'], newblocks)
    except:
        error('here')
    return len(hashes)==0

def peer_check_all(peers, db_extention):
    blocks=[]
    for peer in peers:
        blocks+=peer_check(peer, db_extention)
    for block in blocks:
        chain_push(block, db_extention)

def pushtx(tx, peers):
    for p in peers:
        send_command(p, {'type':'pushtx', 'tx':tx})

def pushblock(block, peers):
    for p in peers:
        send_command(p, {'type':'pushblock', 'block':block})    
def set_minus(l1, l2, ids):#l1-l2
    out=[]
    def member_of(a, l, ids):
        for i in l:
            if a[ids[0]]==i[ids[0]] and a[ids[1]]==i[ids[1]]:
                return True
        return False
    for i in l1:
        if not member_of(i, l2, ids):
            out.append(i)
    return out

def peer_check(peer, db_ex):
    print('checking peer')
    state=state_library.current_state(db_ex)
    cmd=(lambda x: send_command(peer, x))
    block_count=cmd({'type':'blockCount'})
    print('block count: ' +str(block_count))
    if type(block_count)!=type({'a':1}):
        return []
    if 'error' in block_count.keys():
        return []        
#    print('state: ' +str(state))
    ahead=int(block_count['length'])-int(state['length'])
    if ahead < 0:
        chain=copy.deepcopy(load_chain(db_ex))
        print('len chain: ' +str(len(chain)))
        print('length: ' +str(int(block_count['length'])+1))
        print('state len: ' +str(state['length']))
        try:
            pushblock(chain[int(block_count['length'])+1],[peer])
        except:
            pass
        if db_ex=='_miner':
            probability(0.2, chain_unpush(db_ex))
        return []
    if ahead == 0:#if we are on the same block, ask for any new txs
        print('ON SAME BLOCK')
        if state['recent_hash']!=block_count['recent_hash']:
            chain_unpush(db_ex)
            print('WE WERE ON A FORK. time to back up.')
            return []
        my_txs=load_transactions(db_ex)
        txs=cmd({'type':'transactions'})
        add_transactions(txs, db_ex)
        pushers=set_minus(my_txs, txs, ['count', 'id'])
        for push in pushers:
            pushtx(push, [peer])
        return []
#    if ahead>1001:
#        try_state=cmd({'type':'backup_states',
#                   'start': block_count['length']-1000})
#        if type(try_state)==type({'a':'1'}) and 'error' not in state:
#            print('state: ' +str(state))
#            state=try_state
#            state_library.save_state(state)
#        return []
#    print("############################## ahead: "+str(ahead))
#    def f():
#        for i in range(5):
#            chain_unpush(db_ex)
#    probability(0.03, chain_unpush(db_ex))
    start=int(state['length'])-30
    if start<0:
        start=0
    if ahead>500:
        end=int(state['length'])+499
    else:
        end=block_count['length']
    blocks= cmd({'type':'rangeRequest', 
                 'range':[start, end]})
#    print('@@@@@@@@@@@@downloaded blocks')
    if type(blocks)!=type([1,2]):
        return []
    times=1
    while fork_check(blocks, state) and times>0:
        times-=1
        chain_unpush(db_ex)
    return blocks
