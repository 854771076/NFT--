from tools import *
from datetime import datetime, timezone

from fake_useragent import UserAgent
web3tool=Web3Tool(rpc_url='https://api.kroma.network/',chain_id=255,explorer='https://kromascan.com/')
web3=web3tool.web3
contracts={}
contract_base_path='./contract'
wallet_base_path='./wallet.csv'
#接收账号
to='0x72691a36ED1fAC3b197Fb42612Dc15a8958bf9f2'
def load_contract(filename:str):
    '''
    加载合约
    '''
    # 从 JSON 文件中读取钱包信息
    with open(filename, 'r') as file:
        contract_info = json.load(file)
    return contract_info
def get_contract():
    '''
    加载并实例化所有合约
    '''
    contracts_list = glob(os.path.join(contract_base_path, '*'))
    # 使用线程池来并发加载钱包
    for contract_path in contracts_list:
        contract_info=load_contract(contract_path)
        name=contract_info.get('name')
        contract_address=contract_info.get("address")
        abi=contract_info.get('abi')
        contract_address=web3.to_checksum_address(contract_address)
        contract = web3.eth.contract(address=contract_address, abi=abi)
        contracts[name]=contract
def get_NFT_ERC721_id(address):
    contract = contracts['NFT-ERC721']
    # 查询总供应量
    total=contract.functions.balanceOf(address).call()
    tokens = []
    for _ in range(total):
        tokens.append(contract.functions.tokenOfOwnerByIndex(address,_).call())

    return tokens

def transferFrom_ERC721(wallet,to,id):
    func=contracts['NFT-ERC721'].functions.transferFrom(wallet['address'],to,id)
    web3tool.run_contract(func,wallet['address'],wallet['private_key'])
def safe_transferFrom_ERC1155(wallet,to,id=0,amont=10,data=Web3.to_bytes(hexstr='0x00')):
    func=contracts['NFT-ERC1155'].functions.safeTransferFrom(wallet['address'],to,id,amont,data)
    web3tool.run_contract(func,wallet['address'],wallet['private_key'])

def run(wallet):
    account = web3.eth.account.from_key(wallet['private_key'])
    address=account.address
    wallet['address']=address
    try:
        # transferFrom_ERC721(wallet,to,id)
        safe_transferFrom_ERC1155(wallet,to)
        logger.success(f'{address}-发送成功')
    except Exception as e:
        logger.error(f'{address}-发送失败，ERROR：{e}')
        
    return wallet
def from_file_list(file_list):
    res=[]
    header=[file_list.pop(0)]
    for _ in file_list:
        res.append(dict(zip(header,[_])))
    return res


if __name__=='__main__':
    get_contract()
    file_list=open(wallet_base_path,'r').read().split('\n')
    wallets=from_file_list(file_list)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run, wallet) for wallet in wallets]
        for future in as_completed(futures):
            try:
                data = future.result()
            except Exception as e:
                logger.error(f"Error: {e}")
