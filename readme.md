'''
下載顯卡驅動
https://www.nvidia.com/zh-tw/drivers/
=> 顯卡驅動需版本需 >= 527.41

到 NVIDIA 網站下載 CUDE & toolkit
https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html
=> 需確認顯卡最高可使用的 CUDA 版本 (安裝 CUDA 12.6)

1. 安裝 python(3.11.9)
https://www.python.org/downloads/release/python-3119/

新增下列路徑到系統變數的 path 中
C:\Users\user\AppData\Local\Programs\Python\Python310
C:\Users\user\AppData\Local\Programs\Python\Python310\Scripts

遠端使用下指令的話，需以系統管理員做額外做設定
Set-ExecutionPolicy RemoteSigned

透過下列指令建立虛擬環境
py -m venv testenv

啟動虛擬環境
activate test_env

退出虛擬環境
deactivate

2. 安裝相關套件
pytorch 需到 torch 官網確認 torch 版本與 CUDA 的對應
torch 要這樣安裝,否則會報錯
https://pytorch.org/get-started/previous-versions/
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121

安裝其他套件
pip3 install -r .\requirement.txt

3. flash attn 安裝流程(最容易報錯, 須注意)
https://github.com/bdashore3/flash-attention/releases
下載對應版本的 flash attn
torch=2.2.2
python=3.11
CUDA=12.3 (但安裝 12.6 亦可使用)
pip install flash_attn-2.6.3+cu123torch2.2.2cxx11abiFALSE-cp311-cp311-win_amd64.whl

4. 安裝 DB: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

5. 啟動 server
uvicorn server:app --host 140.112.3.52 --reload
'''