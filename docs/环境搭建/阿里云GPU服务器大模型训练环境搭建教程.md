# 阿里云 GPU 服务器大模型训练环境搭建教程

> 本教程详细介绍如何在阿里云 GPU 服务器上从零搭建大模型训练环境，涵盖实例购买、驱动安装、深度学习框架配置等完整流程。
> 🔗 相关笔记：[AutoDL服务器大模型训练环境搭建教程](AutoDL服务器大模型训练环境搭建教程)（更高性价比的替代方案）| [2.3 模型微调](../AI应用开发/2.3 模型微调)（微调原理详解）

---

## 一、GPU 实例选型指南

### 1.1 主流 GPU 实例对比

| 实例规格 | GPU 型号 | 显存 | 适用场景 | 参考价格(按量) |
|---------|---------|------|---------|--------------|
| **gn7i** | A10 (24GB) | 24 GB | 模型推理、中小模型训练 | ~15元/小时 |
| **gn7** | A100 (40/80GB) | 40/80 GB | 大模型训练、分布式训练 | ~50-100元/小时 |
| **gn6v** | V100 (16/32GB) | 16/32 GB | 通用深度学习训练 | ~25元/小时 |
| **gn6i** | T4 (16GB) | 16 GB | 推理、轻量训练 | ~8元/小时 |

### 1.2 选型建议

- **7B 参数模型训练**：至少 1×A100 40GB 或 2×V100 32GB
- **13B 参数模型训练**：2×A100 40GB 或 4×V100 32GB  
- **70B+ 参数模型训练**：8×A100 80GB（多机分布式）
- **模型推理/微调**：A10 或 T4 通常足够

---

## 二、购买与配置 ECS 实例

### 2.1 购买步骤

1. 登录 [阿里云 ECS 控制台](https://ecs.console.aliyun.com/)
2. 点击 **创建实例**
3. 选择配置：

```yaml
# 推荐配置示例
地域: 华东2(上海) 或 华北2(北京)  # GPU资源较充足
实例规格: ecs.gn7i-c16g1.4xlarge   # 1×A10 GPU
镜像: Ubuntu 22.04 64位 + GPU驱动预装
系统盘: ESSD云盘 200GB 以上
公网带宽: 按流量计费，峰值100Mbps
计费方式: 按量付费（测试）/ 包年包月（生产）
```

### 2.2 关键配置说明

#### 镜像选择（推荐预装镜像）

```
Ubuntu 22.04 64位 UEFI版
☑️ 自动安装GPU驱动
  - CUDA版本: 12.1.1
  - 驱动版本: 535.154.05
  - cuDNN版本: 8.9.7.29
```

#### 安全组配置

```bash
# 入方向规则
SSH(22)        : 允许
Jupyter(8888)  : 允许（可选）
自定义端口     : 根据需要添加
```

---

## 三、连接服务器

### 3.1 SSH 连接

```bash
# 使用密钥连接
ssh -i ~/.ssh/your_key.pem root@<公网IP>

# 使用密码连接
ssh root@<公网IP>
```

### 3.2 验证 GPU 环境

```bash
# 查看GPU驱动版本
nvidia-smi

# 预期输出示例
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.154.05   Driver Version: 535.154.05   CUDA Version: 12.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA A10          On   | 00000000:00:07.0 Off |                    0 |
|  0%   32C    P8     15W / 150W|      0MiB / 23028MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+

# 验证CUDA
nvcc -V
```

---

## 四、环境配置

### 4.1 安装 Miniconda

```bash
# 下载安装
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# 初始化
~/miniconda3/bin/conda init bash
source ~/.bashrc

# 配置国内镜像
conda config --add channels https://mirrors.aliyun.com/anaconda/pkgs/main/
conda config --add channels https://mirrors.aliyun.com/anaconda/pkgs/free/
conda config --set show_channel_urls yes
```

### 4.2 创建训练环境

```bash
# 创建虚拟环境
conda create -n llm python=3.11 -y
conda activate llm

# 配置pip镜像
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

### 4.3 安装 PyTorch（GPU 版本）

```bash
# PyTorch 2.x + CUDA 12.1（推荐）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 验证安装
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

### 4.4 安装深度学习常用库

```bash
# 基础库
pip install numpy pandas scikit-learn matplotlib jupyter

# Transformer 相关
pip install transformers datasets accelerate peft trl

# 分布式训练
pip install deepspeed

# 量化推理
pip install bitsandbytes

# LLM 开发
pip install langchain openai tiktoken

# 模型下载工具
pip install modelscope huggingface_hub
```

---

## 五、LLaMA-Factory 环境搭建

> [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) 是目前最流行的大模型微调框架（GitHub 60k+ Stars），支持 **零代码可视化微调**，集成了 LoRA、QLoRA、Full 等多种微调方法。

### 5.1 为什么选择 LLaMA-Factory？

| 优势 | 说明 |
|------|------|
| 🎯 **零代码微调** | 提供 WebUI 可视化界面，无需编写代码 |
| 🔧 **多种微调方法** | 支持 LoRA / QLoRA / Full / Freeze 等 |
| 📦 **100+ 模型支持** | LLaMA、Qwen、DeepSeek、GLM、Mistral 等 |
| 🚀 **训练方法丰富** | SFT、RLHF、DPO、PPO、KTO、ORPO 等 |
| 🖼️ **多模态支持** | 支持 VLM（视觉语言模型）微调 |

### 5.2 安装 LLaMA-Factory

```bash
# 激活虚拟环境
conda activate llm

# 克隆仓库
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory

# 安装依赖（包含 PyTorch 和评估指标）
pip install -e ".[torch,metrics]"

# 如果出现依赖冲突，使用以下命令
# pip install --no-deps -e .
```

### 5.3 验证安装

```bash
# 检查版本
llamafactory-cli version

# 预期输出
# Welcome to LLaMA Factory, version x.x.x
```

```python
# 验证 GPU 支持
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

### 5.4 启动 WebUI（可视化微调）

```bash
# 启动 Web 界面
llamafactory-cli webui

# 指定端口和地址（远程访问）
GRADIO_SERVER_NAME=0.0.0.0 GRADIO_SERVER_PORT=7860 llamafactory-cli webui
```

> 💡 **远程访问**：确保安全组已开放 7860 端口，浏览器访问 `http://<公网IP>:7860`

### 5.5 WebUI 界面说明

启动后界面分为以下模块：

```
┌─────────────────────────────────────────────────────────┐
│  🔧 模型选择  │  选择基座模型（Qwen、LLaMA、DeepSeek等）   │
├─────────────────────────────────────────────────────────┤
│  📁 数据集    │  选择/上传训练数据集                      │
├─────────────────────────────────────────────────────────┤
│  ⚙️ 微调方法  │  LoRA / QLoRA / Full / Freeze            │
├─────────────────────────────────────────────────────────┤
│  📊 训练参数  │  学习率、Epoch、Batch Size 等             │
├─────────────────────────────────────────────────────────┤
│  🚀 开始训练  │  一键启动训练                             │
├─────────────────────────────────────────────────────────┤
│  💬 对话测试  │  加载模型进行对话测试                     │
└─────────────────────────────────────────────────────────┘
```

### 5.6 命令行微调示例

#### LoRA 微调（推荐，显存友好）

```bash
# 使用内置数据集微调 Qwen2
llamafactory-cli train \
    --stage sft \
    --model_name_or_path /root/models/Qwen2-7B-Instruct \
    --dataset alpaca_zh \
    --template qwen \
    --finetuning_type lora \
    --lora_rank 16 \
    --lora_alpha 32 \
    --output_dir ./saves/qwen2-7b-lora \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 4 \
    --num_train_epochs 3 \
    --learning_rate 2e-4 \
    --fp16 \
    --logging_steps 10 \
    --save_steps 100
```

#### QLoRA 微调（4-bit 量化，更省显存）

```bash
llamafactory-cli train \
    --stage sft \
    --model_name_or_path /root/models/Qwen2-7B-Instruct \
    --dataset alpaca_zh \
    --template qwen \
    --finetuning_type lora \
    --quantization_bit 4 \
    --lora_rank 16 \
    --output_dir ./saves/qwen2-7b-qlora \
    --per_device_train_batch_size 2 \
    --num_train_epochs 3 \
    --fp16
```

### 5.7 自定义数据集

在 `data/dataset_info.json` 中注册数据集：

```json
{
  "my_dataset": {
    "file_name": "my_train_data.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}
```

数据格式示例（`data/my_train_data.json`）：

```json
[
  {
    "instruction": "请介绍一下人工智能",
    "input": "",
    "output": "人工智能（AI）是计算机科学的一个分支..."
  },
  {
    "instruction": "翻译以下句子为英文",
    "input": "今天天气很好",
    "output": "The weather is nice today."
  }
]
```

### 5.8 模型导出与合并

```bash
# 合并 LoRA 权重到基座模型
llamafactory-cli export \
    --model_name_or_path /root/models/Qwen2-7B-Instruct \
    --adapter_name_or_path ./saves/qwen2-7b-lora \
    --template qwen \
    --finetuning_type lora \
    --export_dir ./exports/qwen2-7b-merged \
    --export_size 2 \
    --export_legacy_format false
```

### 5.9 对话测试

```bash
# 命令行对话
llamafactory-cli chat \
    --model_name_or_path /root/models/Qwen2-7B-Instruct \
    --adapter_name_or_path ./saves/qwen2-7b-lora \
    --template qwen \
    --finetuning_type lora
```

### 5.10 显存需求参考

| 模型规模 | Full 微调 | LoRA | QLoRA (4-bit) |
|---------|----------|------|---------------|
| 7B | ~60 GB | ~16 GB | ~6 GB |
| 13B | ~120 GB | ~32 GB | ~10 GB |
| 70B | ~500 GB | ~160 GB | ~48 GB |

> 💡 使用 `gradient_checkpointing` 可进一步降低约 30% 显存

### 5.11 常见问题

#### Q: WebUI 无法远程访问？
```bash
# 确保使用 0.0.0.0 绑定
GRADIO_SERVER_NAME=0.0.0.0 llamafactory-cli webui
# 检查安全组是否开放 7860 端口
```

#### Q: 训练时 OOM（显存不足）？
```bash
# 解决方案
1. 减小 per_device_train_batch_size
2. 使用 QLoRA（quantization_bit=4）
3. 增加 gradient_accumulation_steps
4. 启用 gradient_checkpointing=true
```

#### Q: 如何使用多卡训练？
```bash
# 使用 accelerate 多卡并行
CUDA_VISIBLE_DEVICES=0,1,2,3 accelerate launch \
    --num_processes 4 \
    -m llamafactory.train \
    --config_file train_config.yaml
```

---

## 六、模型下载与存储

### 5.1 使用 ModelScope（国内镜像，推荐）

```python
from modelscope import snapshot_download

# 下载Qwen模型示例
model_dir = snapshot_download(
    'qwen/Qwen2-7B-Instruct',
    cache_dir='/root/models'
)
print(f"模型下载到: {model_dir}")
```

### 5.2 使用 Hugging Face

```bash
# 设置镜像（加速下载）
export HF_ENDPOINT=https://hf-mirror.com

# 下载模型
huggingface-cli download meta-llama/Llama-2-7b-hf --local-dir /root/models/llama2-7b
```

### 5.3 数据盘挂载（存储大模型）

```bash
# 查看数据盘
lsblk

# 格式化并挂载（假设数据盘为/dev/vdb）
mkfs.ext4 /dev/vdb
mkdir -p /data
mount /dev/vdb /data

# 设置开机自动挂载
echo '/dev/vdb /data ext4 defaults 0 0' >> /etc/fstab
```

---

## 七、训练示例

### 6.1 LoRA 微调示例

```python
# train_lora.py
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
from trl import SFTTrainer

# 加载模型
model_name = "/root/models/Qwen2-7B-Instruct"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# LoRA配置
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# 加载数据集
dataset = load_dataset("json", data_files="train.jsonl")

# 训练参数
training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=100,
)

# 开始训练
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    args=training_args,
    tokenizer=tokenizer,
)
trainer.train()
```

### 6.2 运行训练

```bash
# 单卡训练
python train_lora.py

# 多卡训练（使用accelerate）
accelerate launch --num_processes=4 train_lora.py

# 使用DeepSpeed（大模型分布式训练）
deepspeed --num_gpus=8 train_lora.py --deepspeed ds_config.json
```

---

## 八、常用运维命令

### 7.1 GPU 监控

```bash
# 实时监控GPU状态
watch -n 1 nvidia-smi

# 查看GPU进程
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

# 查看GPU详细信息
nvidia-smi -q
```

### 7.2 后台运行训练

```bash
# 使用nohup
nohup python train.py > train.log 2>&1 &

# 使用tmux（推荐）
tmux new -s train
python train.py
# Ctrl+B, D 断开  |  tmux attach -t train 重连

# 使用screen
screen -S train
python train.py
# Ctrl+A, D 断开  |  screen -r train 重连
```

### 7.3 显存优化技巧

```python
# 1. 使用梯度累积减少batch_size
gradient_accumulation_steps=8

# 2. 混合精度训练
fp16=True  # 或 bf16=True（A100推荐）

# 3. 梯度检查点
model.gradient_checkpointing_enable()

# 4. 8bit优化器（节省显存）
from bitsandbytes.optim import Adam8bit
optimizer = Adam8bit(model.parameters(), lr=2e-4)

# 5. DeepSpeed ZeRO-3（超大模型）
deepspeed --num_gpus=8 train.py --deepspeed ds_zero3.json
```

---

## 九、成本优化建议

### 8.1 计费方式选择

| 场景 | 推荐计费方式 | 说明 |
|-----|------------|------|
| 短期实验 | 按量付费 | 用完即释放 |
| 长期训练 | 包年包月 | 折扣约4-6折 |
| 不定期使用 | 抢占式实例 | 最高节省90% |

### 8.2 节省技巧

1. **抢占式实例**：适合可中断的训练任务，价格低至1折
2. **预留实例券**：长期使用可获得更大折扣
3. **自动释放**：设置实例自动释放时间避免遗忘
4. **数据盘复用**：使用快照创建新实例时挂载原数据盘

---

## 十、常见问题排查

### Q1: CUDA out of memory

```bash
# 检查显存占用
nvidia-smi

# 解决方案
1. 减小batch_size
2. 启用梯度检查点
3. 使用混合精度训练
4. 使用DeepSpeed ZeRO优化
```

### Q2: 驱动版本不匹配

```bash
# 重新安装驱动
sudo apt-get purge nvidia-*
sudo apt-get install nvidia-driver-535

# 重启后验证
nvidia-smi
```

### Q3: pip 安装超时

```bash
# 使用阿里云镜像
pip install xxx -i https://mirrors.aliyun.com/pypi/simple/

# 增加超时时间
pip install xxx --timeout=1000
```

---

## 十一、推荐资源

- [阿里云GPU最佳实践](https://help.aliyun.com/zh/ecs/use-cases/overview-of-best-practices-for-gpu-use)
- [LLaMA-Factory GitHub](https://github.com/hiyouga/LLaMA-Factory) ⭐ 推荐
- [LLaMA-Factory 官方文档](https://llamafactory.readthedocs.io/)
- [阿里云 PAI LLaMA-Factory 教程](https://help.aliyun.com/zh/pai/use-cases/fine-tune-a-llama-3-model-with-llama-factory)
- [Hugging Face PEFT文档](https://huggingface.co/docs/peft)
- [DeepSpeed官方文档](https://www.deepspeed.ai/)
- [ModelScope模型库](https://modelscope.cn/models)

---

> 📝 **更新日期**: 2026-02-07  
> 💡 **提示**: 建议收藏本教程，实际操作时按步骤执行
