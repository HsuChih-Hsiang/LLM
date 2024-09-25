<h3>顯卡驅動安裝順序</h3>

下載顯卡驅動 (https://www.nvidia.com/zh-tw/drivers/)<br>
**Note: 顯卡驅動需版本需 >= 527.41**

到 NVIDIA 網站下載 CUDE & toolkit(https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html)<br>
**Note: 需確認顯卡最高可使用的 CUDA 版本 (安裝 CUDA 12.6)**

<h3>程式相關安裝順序</h3>

<h4>1. 安裝 python(3.11.9)</h4>
https://www.python.org/downloads/release/python-3119/

新增下列路徑到系統變數的 path 中<br>
C:\Users\user\AppData\Local\Programs\Python\Python310<br>
C:\Users\user\AppData\Local\Programs\Python\Python310\Scripts

遠端使用下指令的話，需以系統管理員做額外做設定<br>
Set-ExecutionPolicy RemoteSigned

透過下列指令建立虛擬環境<br>
py -m venv testenv

啟動虛擬環境<br>
activate test_env

退出虛擬環境<br>
deactivate

<h4>2.安裝相關套件</h4>
pytorch 需到 torch 官網( https://pytorch.org/get-started/previous-versions/ )<br>
確認 torch 版本與 CUDA 的對應<br>
兩種方法，對應不同的 flash-attn 安裝方式<br>
1. pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121<br>
2. pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121<br>
**Note: torch 2.4.1 才能使用 optimum-quanto**

安裝其他套件<br>
pip3 install -r .\requirement.txt

<h4>3.flash attn 安裝流程(最容易報錯, 須注意)</h4>
https://github.com/bdashore3/flash-attention/releases<br>
1. 下載對應版本的 flash attn<br>
torch=2.2.2<br>
python=3.11<br>
CUDA=12.3 (但安裝 12.6 亦可使用)<br>
pip install flash_attn-2.6.3+cu123torch2.2.2cxx11abiFALSE-cp311-cp311-win_amd64.whl<br>
2. 先設定系統變數再進行編譯<br>
set MAX_JOBS=128<br>
python -m pip install flash-attn

<h4>4.安裝 DB: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads</h4>

<h4>5.安裝 Visual studio: https://visualstudio.microsoft.com/zh-hant/downloads/</h4>

<h4>6.下載 pgvector</h4>
git clone https://github.com/pgvector/pgvector.git

<h4>7.以系統管理員執行 data/pgvector.bat</h4>
其中資料夾位置及PostgreSQL的位置須自行更改

<h4>8. 新增系統變數</h4>
將下列路徑新增至系統變數
C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.41.34120\bin\Hostx64\x64

<h4>9.啟動 server</h4>
uvicorn server:app --host 140.112.3.52 --reload or python server.py
