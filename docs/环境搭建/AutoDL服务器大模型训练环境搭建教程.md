# AutoDL GPU服务器大模型训练环境搭建教程

> 本教程详细介绍如何在 AutoDL GPU 算力云平台上搭建大模型训练环境。AutoDL 以其超高的性价比（如不到 2 元/时的 4090）深受学生和个人开发者喜爱。本教程涵盖实例租用、环境配置、LLaMA-Factory 部署及模型训练全流程。
> 🔗 相关笔记：[阿里云GPU服务器大模型训练环境搭建教程](阿里云GPU服务器大模型训练环境搭建教程)（企业级方案）| [2.3 模型微调](../AI应用开发/2.3 模型微调)（微调原理详解）| [Easy Dataset 基础教程](../工具与平台/Easy Dataset 基础教程)（数据集制作）

---

## 一、GPU 实例选型推荐

### 1.1 主流 GPU 实例对比

| 实例规格 | 显存 | 适用场景 | 参考价格(按量) | 备注 |
|---------|------|---------|--------------|------|
| **RTX 4090** | 24 GB | 7B-14B模型全量微调 / 72B模型QLoRA | ~1.8-2.5元/小时 | **性价比之王**，不支持NVLink |
| **RTX 3090** | 24 GB | 7B模型微调 / 学习实验 | ~1.0-1.6元/小时 | 入门首选 |
| **A100 (PCIE)** | 40/80 GB | 70B+大模型训练 / 多卡并行 | ~6-10元/小时 | 算力强劲，但较贵 |
| **A800/H800** | 80 GB | 企业级大规模预训练 | ~15+元/小时 | 通常需要企业认证 |

### 1.2 选型建议

- **入门/学习**：RTX 3090 或 RTX 4090（单卡即可跑通大部分 7B-14B 模型）。
- **高性价比**：RTX 4090D 是目前的甜点卡，性能接近 A100 但价格便宜很多。
- **微调 7B 模型**：
  - LoRA 微调：主要看显存，24G 显存（3090/4090）足够。
  - 全量微调：推荐双卡 4090 或单卡 A100 80G。

---

## 二、租用与配置实例

### 2.1 租用步骤

1. 登录 [AutoDL 官网](https://www.autodl.com/) -> **控制台** -> **算力市场**。
2. 选择 **计费方式**：推荐“按量付费”（用完即停，灵活）。
3. 选择 **地区**：建议选择显示“空闲”较多的地区（如内蒙 A 区、西北 A 区），通常价格更低。
4. 选择 **GPU 型号**：筛选 RTX 4090 或 3090。
5. **镜像选择（关键）**：
   - 基础镜像：`Miniconda` -> `conda3` -> `CUDA 11.8` 或 `CUDA 12.1`（推荐 12.1）。
   - **不要选纯净系统**，预装驱动和 CUDA 的镜像能省去 90% 的环境配置麻烦。

### 2.2 关键配置说明

> ⚠️ **注意数据盘**：AutoDL 的系统盘通常只有 30GB，**严禁将大模型权重放在系统盘（/root）！**
> 一定要使用 **数据盘**（挂载在 `/root/autodl-tmp`），该目录空间大且读写快。

---

## 三、连接服务器

### 3.1 网页终端（JupyterLab）

租用成功后，在控制台点击【JupyterLab】即可直接进入网页版终端，适合简单的文件管理和命令操作。

### 3.2 SSH 连接（VSCode 远程开发 - 推荐）

为了获得最佳的编码体验，强烈推荐使用 VSCode 进行远程连接。

1. **获取登录指令**：
   在控制台找到实例，复制“登录指令”，格式通常为：
   `ssh -p 12345 root@region-x.autodl.com`
   
   - 用户名：`root`
   - 主机名：`region-x.autodl.com`
   - 端口：`12345`
   - 密码：点击“复制密码”

2. **配置 VSCode**：
   - 安装插件 `Remote - SSH`。
   - 点击左下角 `><` 图标 -> `Connect to Host...` -> `Add New SSH Host`。
   - 粘贴登录指令。
   - 再次点击 `Connect to Host` 选择刚才添加的主机，输入密码即可。

---

## 四、环境配置（AutoDL 特有）

### 4.1 开启学术加速（重要！）

AutoDL 从国内访问 GitHub 或 Hugging Face 速度较慢，必须通过官方提供的学术加速脚本优化网络。

```bash
# 在终端执行（每次开启新终端建议都执行一次，或者写入 .bashrc）
source /etc/network_turbo
```

> 验证加速：`curl https://www.google.com` 如果能返回 HTML 代码则说明加速成功。

### 4.2 初始化 Conda 环境

AutoDL 默认进入的是 `base` 环境，我们创建一个专用的环境。

```bash
# 初始化 conda（如果是首次）
conda init bash
source ~/.bashrc

# 创建环境 (推荐 python 3.10 或 3.11)
conda create -n llm python=3.10 -y
conda activate llm
```

### 4.3 安装深度学习框架

```bash
# 安装 PyTorch (根据你的 CUDA 版本选择，这里以 CUDA 12.1 为例)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 验证 GPU
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
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
# 切换到数据盘（重要！避免系统盘爆满）
cd /root/autodl-tmp

# 开启学术加速
source /etc/network_turbo

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

### 5.4 安装其他常用库

```bash
# 模型下载
pip install modelscope huggingface_hub

# 分布式训练
pip install deepspeed

# 量化推理
pip install bitsandbytes

# Flash Attention（加速训练，可选）
pip install flash-attn --no-build-isolation
```

### 5.5 命令行微调示例

#### LoRA 微调（推荐，显存友好）

```bash
llamafactory-cli train \
    --stage sft \
    --model_name_or_path /root/autodl-tmp/models/Qwen2-7B-Instruct \
    --dataset alpaca_zh \
    --template qwen \
    --finetuning_type lora \
    --lora_rank 16 \
    --lora_alpha 32 \
    --output_dir /root/autodl-tmp/saves/qwen2-7b-lora \
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
    --model_name_or_path /root/autodl-tmp/models/Qwen2-7B-Instruct \
    --dataset alpaca_zh \
    --template qwen \
    --finetuning_type lora \
    --quantization_bit 4 \
    --lora_rank 16 \
    --output_dir /root/autodl-tmp/saves/qwen2-7b-qlora \
    --per_device_train_batch_size 2 \
    --num_train_epochs 3 \
    --fp16
```

### 5.6 自定义数据集

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

### 5.7 模型导出与合并

```bash
# 合并 LoRA 权重到基座模型
llamafactory-cli export \
    --model_name_or_path /root/autodl-tmp/models/Qwen2-7B-Instruct \
    --adapter_name_or_path /root/autodl-tmp/saves/qwen2-7b-lora \
    --template qwen \
    --finetuning_type lora \
    --export_dir /root/autodl-tmp/exports/qwen2-7b-merged \
    --export_size 2 \
    --export_legacy_format false
```

### 5.8 对话测试

```bash
# 命令行对话
llamafactory-cli chat \
    --model_name_or_path /root/autodl-tmp/models/Qwen2-7B-Instruct \
    --adapter_name_or_path /root/autodl-tmp/saves/qwen2-7b-lora \
    --template qwen \
    --finetuning_type lora
```

### 5.9 显存需求参考

| 模型规模 | Full 微调 | LoRA | QLoRA (4-bit) |
|---------|----------|------|---------------|
| 7B | ~60 GB | ~16 GB | ~6 GB |
| 13B | ~120 GB | ~32 GB | ~10 GB |
| 70B | ~500 GB | ~160 GB | ~48 GB |

> 💡 使用 `gradient_checkpointing` 可进一步降低约 30% 显存

### 5.10 常见问题

#### Q: WebUI 无法远程访问？
```bash
# 确保使用 6006 端口并通过 SSH 隧道映射
export GRADIO_SERVER_PORT=6006
llamafactory-cli webui
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

## 六、模型与数据下载

### 6.1 使用 AutoDL 内网加速下载（ModelScope）

AutoDL 对 ModelScope（魔搭社区）有内网加速，下载速度极快（可达 100MB/s+）。

```python
# 创建下载脚本 download_model.py
from modelscope import snapshot_download

model_dir = snapshot_download(
    'qwen/Qwen2-7B-Instruct', 
    cache_dir='/root/autodl-tmp/models',  # 务必指定到数据盘
    revision='master'
)
print(f"Model downloaded to: {model_dir}")
```

运行下载：
```bash
python download_model.py
```

---

## 七、WebUI 可视化微调

### 7.1 启动 WebUI

```bash
cd /root/autodl-tmp/LLaMA-Factory
export CUDA_VISIBLE_DEVICES=0
export GRADIO_SERVER_PORT=6006  # AutoDL 默认开放 6006 端口用于 Web 服务

llamafactory-cli webui
```

> ⚠️ 注意：不要使用默认的 7860 端口，AutoDL 对外开放的 HTTP 端口通常是 6006。

### 7.2 本地访问 WebUI（SSH 隧道）

AutoDL 默认不直接暴露 HTTP 端口，需要通过 SSH 隧道映射到本地。

1. **在你的本地电脑（不是服务器）** 打开终端（CMD/PowerShell/Terminal）。
2. 执行端口映射命令：
   ```bash
   # 格式：ssh -CNg -L <本地端口>:localhost:<服务器端口> -p <SSH端口> root@<IP>
   # 例如你的登录指令是 ssh -p 12345 root@region-1.autodl.com
   
   ssh -CNg -L 6006:localhost:6006 -p 12345 root@region-1.autodl.com
   ```
3. 输入密码后，终端会“卡住”（这是正常的，表示隧道已建立）。
4. 在本地浏览器访问：`http://localhost:6006` 即可看到训练界面。

---

## 八、AutoDL 使用技巧与避坑指南

### 8.1 避免系统盘爆满
- **现象**：安装包失败、无法 Tab 补全、无法启动服务。
- **原因**：AutoDL 系统盘（`/`）一般只有 30G，conda 环境和缓存很容易将其填满。
- **解决**：
  1. **清理缓存**：`conda clean -a` 和 `pip cache purge`。
  2. **迁移 Conda**：如果环境太大，建议将 conda 安装目录迁移到 `/root/autodl-tmp`。
  3. **软链接**：将 `.cache` 目录软链接到数据盘。
     ```bash
     mkdir -p /root/autodl-tmp/.cache
     rm -rf /root/.cache
     ln -s /root/autodl-tmp/.cache /root/.cache
     ```

### 8.2 数据持久化（保存镜像）
- AutoDL 的实例在释放后，**数据盘（/root/autodl-tmp）的数据默认会保留一定时间（视官方政策而定，通常会保留），但系统盘数据会丢失。**
- **重要**：如果你在系统盘安装了大量环境，建议在关机前点击控制台的 **“保存镜像”**。这样下次租用时可以直接选择该镜像，环境复原。

### 8.3 自动关机（省钱技巧）
- 跑长时间训练任务时，可以在命令后加上自动关机指令，防止训练完空跑扣费。
- AutoDL 提供了 `shutdown` 命令不可用，但可以在控制台设置“定时关机”或使用 Python 脚本作为 Trigger。
- **简单做法**：训练脚本通常会运行很久，可以使用：
  ```bash
  # 训练完后调用 API 关机（需查阅 AutoDL API 文档）或手动设置预计关机时间。
  ```
- **更推荐**：使用 **“无卡模式”** 开机（非常便宜，0.1元/时）进行环境配置和代码调试，确认无误后再“升配”或切换到 GPU 模式运行。

---

## 九、常用命令速查

| 功能 | 命令 |
|------|------|
| 开启学术加速 | `source /etc/network_turbo` |
| 取消学术加速 | `unset http_proxy && unset https_proxy` |
| 查看目录大小 | `du -sh *` |
| 显存监控 | `nvidia-smi` 或 `nvitop` (推荐 `pip install nvitop`) |
| 进程监控 | `htop` |

---

> 📝 **更新日期**: 2026-02-07
> ⚠️ **声明**：AutoDL 为第三方平台，请注意数据安全，重要代码建议使用 Git 托管到云端仓库。
