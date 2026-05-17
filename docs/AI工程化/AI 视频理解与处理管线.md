# AI 视频理解与处理管线

> 从原始视频到结构化输出——完整拆解视频处理管线的每一层：音频提取、语音转录、LLM 语义分析、FFmpeg 切片导出，附带生产级实现代码与性能优化方案。

---

## 1. 视频处理管线的全景架构

一段 3 小时的直播录像，人工剪辑需要一个熟练剪辑师花 8-12 小时去回看、标记、裁切、配文案。AI 管线可以把这个过程压缩到 10 分钟以内——但前提是你得搞清楚"视频 → 音频 → 文本 → 语义理解 → 结构化输出"这条链路的每一层在做什么、怎么做、以及为什么这么做。

### 1.1 为什么需要 AI 视频处理管线

先搞清楚一个反直觉的事实：**AI 目前并不能直接"看懂"长视频**。

```
一个常见的误解：

  ❌ "把视频丢给 AI，AI 就能自动找出精彩片段"
  
  实际情况：
  ═══════════════════════════════════════
  • GPT-4o：不接受视频输入（只能看图片）
  • Gemini 2.5：支持视频，但有时长限制（~1 小时）
  • Claude：不支持视频输入
  • 所有模型：长视频理解精度不够，无法精确到秒级时间点
```

所以，要让 AI 处理视频，必须把这个问题**拆解**成 AI 擅长的子问题：

```
传统方式 vs AI 管线：

  传统人工剪辑
  ═══════════════════════════════════════
  1. 人工回看 3 小时视频             → 3+ 小时
  2. 标记精彩时间点                   → 1 小时
  3. 逐段裁切导出                     → 1 小时
  4. 写标题和文案                     → 1 小时
  ──────────────────────────────────────
  总计：6-12 小时 / 条直播

  AI 管线
  ═══════════════════════════════════════
  1. FFmpeg 提取音频（自动）           → 30 秒
  2. Whisper 语音转文字（自动）        → 3-5 分钟
  3. LLM 分析精彩片段（自动）         → 30 秒
  4. FFmpeg 批量切片（自动）           → 1-2 分钟
  5. 自动生成标题和文案               → 包含在步骤 3
  ──────────────────────────────────────
  总计：5-10 分钟 / 条直播（全自动）
```

效率差距在 **50-100 倍**。但更重要的是，这个管线可以 7×24 无人值守运行——主播下播后 10 分钟，切片视频就已经在等着发布了。

| 维度 | 传统人工 | AI 管线 |
|:---|:---|:---|
| **时间** | 6-12 小时 | 5-10 分钟 |
| **成本** | 剪辑师日薪 300-500 元 | API 费用 0.5-2 元 |
| **一致性** | 依赖剪辑师经验 | 标准化、可复现 |
| **扩展性** | 一个人处理 2-3 条/天 | 一台服务器处理 100+ 条/天 |
| **24h 运营** | 需要排班 | 全自动 |

> 💡 **关键洞察**：AI 视频管线的核心思路不是"用 AI 看视频"，而是"把视频翻译成 AI 擅长的文本，再用 AI 的语义理解能力去分析"。这就是为什么管线是多层的——每一层负责一次模态转换。

### 1.2 管线五层架构：从比特流到语义理解

整条管线可以抽象为五层，每一层完成一次数据转换：

```
AI 视频处理管线五层架构：

  ┌─────────────────────────────────────────────────────┐
  │                    原始视频文件                        │
  │              (MP4 / MKV / FLV, 2-10 GB)              │
  └────────────────────────┬────────────────────────────┘
                           │
                    ▼ 第 1 层：预处理
  ┌─────────────────────────────────────────────────────┐
  │  视频 ──▶ FFmpeg ──▶ 音频（16kHz mono MP3, ~30 MB）   │
  │  职责：模态分离，从视频中提取语音信号                     │
  │  关键：采样率、编码参数、PTS 偏移修正                    │
  └────────────────────────┬────────────────────────────┘
                           │
                    ▼ 第 2 层：语音转录（ASR）
  ┌─────────────────────────────────────────────────────┐
  │  音频 ──▶ Whisper / 云端 ASR ──▶ 带时间戳的文本        │
  │  职责：语音信号 → 结构化文本                            │
  │  输出：[{start, end, text}, ...]                      │
  └────────────────────────┬────────────────────────────┘
                           │
                    ▼ 第 3 层：语义分析（LLM）
  ┌─────────────────────────────────────────────────────┐
  │  转录文本 ──▶ LLM（DeepSeek / GPT-4o）──▶ 切片方案     │
  │  职责：理解内容语义，找出精彩片段                        │
  │  输出：[{clip_id, title, start_time, end_time}, ...]  │
  └────────────────────────┬────────────────────────────┘
                           │
                    ▼ 第 4 层：视频切片
  ┌─────────────────────────────────────────────────────┐
  │  原视频 + 切片方案 ──▶ FFmpeg ──▶ 多个 MP4 片段         │
  │  职责：按时间点精确裁切原视频                            │
  │  关键：关键帧对齐、编码质量、并行处理                     │
  └────────────────────────┬────────────────────────────┘
                           │
                    ▼ 第 5 层：调度与输出
  ┌─────────────────────────────────────────────────────┐
  │  切片文件 ──▶ 存储 / 打包 / 推送                       │
  │  职责：任务编排、进度追踪、结果交付                      │
  │  能力：SSE 实时推送、ZIP 打包、剪映草稿导出              │
  └─────────────────────────────────────────────────────┘
```

每一层的数据变换和体积变化一目了然：

| 层级 | 输入 | 输出 | 体积变化 | 耗时参考 |
|:---|:---|:---|:---|:---|
| **L1 预处理** | 视频（2.5 GB） | 音频（30 MB） | ↓ 99% | 30 秒 |
| **L2 转录** | 音频（30 MB） | 文本（50 KB） | ↓ 99.8% | 3-5 分钟 |
| **L3 分析** | 文本（50 KB） | JSON（5 KB） | ↓ 90% | 10-30 秒 |
| **L4 切片** | 视频 + JSON | N 个 MP4 | 按需 | 1-2 分钟 |
| **L5 调度** | 切片文件 | ZIP / SRT / 草稿 | — | 秒级 |

> 💡 **核心设计原则**：每一层只做一件事——模态转换。视频 → 音频 → 文本 → 语义 → 文件。这种分层设计的好处是每一层可以独立优化、独立替换。比如想从 Whisper 换成阿里云 ASR，只改 L2 层，其他层完全不受影响。
### 1.3 技术选型与依赖全景

```
本教程的技术栈：

  层级              组件                    选型                        用途
  ──────────────────────────────────────────────────────────────────────────
  L1 预处理         FFmpeg                  系统级 / FFmpeg.wasm         音视频分离
  L2 转录           faster-whisper          CUDA GPU 本地推理           语音转文字
                    mlx-whisper             Apple Silicon 本地推理       语音转文字
                    阿里云 Flash ASR        云端 API                    语音转文字（兜底）
  L3 分析           DeepSeek V3             OpenAI 兼容 API             语义理解
  L4 切片           FFmpeg                  系统级                      视频裁切
                    FFmpeg.wasm             浏览器端                    本地切片
  L5 调度           ARQ                     Redis + asyncio             异步任务队列
                    SSE                     FastAPI StreamingResponse   实时进度推送
                    PostgreSQL              SQLAlchemy async            数据持久化
  ──────────────────────────────────────────────────────────────────────────
```

**后端依赖安装：**

```bash
# ── FFmpeg（系统级，必须） ──
# macOS
brew install ffmpeg
# Ubuntu / Debian
apt install ffmpeg

# ── 核心 Python 依赖 ──
pip install fastapi uvicorn python-multipart    # Web 框架
pip install sqlalchemy[asyncio] asyncpg          # 数据库
pip install arq                                  # 异步任务队列
pip install redis                                # ARQ 后端
pip install openai                               # LLM（DeepSeek 兼容 OpenAI 协议）
pip install httpx                                # 异步 HTTP（云端 ASR）

# ── 语音转录（按环境三选一） ──
# CUDA GPU 环境
pip install faster-whisper
# Apple Silicon Mac
pip install mlx-whisper
# 无 GPU（使用阿里云 ASR，无需额外安装）
```

**前端依赖（浏览器端音频提取）：**

```bash
npm install @ffmpeg/ffmpeg @ffmpeg/util          # FFmpeg.wasm
npm install fflate                               # ZIP 打包（本地切片用）
```

> 💡 **关于 FFmpeg.wasm 的版本**：推荐使用 `@ffmpeg/ffmpeg@0.12.x`，这个版本支持 WORKERFS（零拷贝挂载），可以处理 4GB+ 的大文件而不会 OOM。 `0.11.x` 及之前的版本只支持 `writeFile`，会把整个文件读入 WASM 内存。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **AI 不能直接看视频** | 需要通过管线把视频"翻译"成文本，再用 LLM 分析 |
| **五层架构** | 预处理 → 转录 → 分析 → 切片 → 调度，每层做一次模态转换 |
| **效率提升** | 3 小时直播的切片从 6-12 小时人工 → 5-10 分钟全自动 |
| **分层解耦** | 每层可以独立替换（换 ASR、换 LLM），互不影响 |
| **技术选型** | FFmpeg + Whisper/ASR + DeepSeek + ARQ + PostgreSQL |

---

## 2. 第一层：视频预处理与音频提取

管线的第一层做的事情最简单也最关键——把视频中的音频信号剥离出来。这一步决定了后续所有环节的数据质量：音频提取参数选不对，转录精度会直接下降；文件太大，上传到云端 ASR 会超时；PTS 偏移没修正，切出来的视频时间全是错的。

### 2.1 FFmpeg 音频提取：参数调优与最佳实践

音频提取的核心工具是 FFmpeg。一行命令就能完成，但每个参数的选择都有讲究：

```bash
ffmpeg -y \
  -i input.mp4 \
  -vn \                    # 去掉视频流（不需要画面）
  -acodec libmp3lame \     # MP3 编码（比 WAV 小 10 倍）
  -ar 16000 \              # 16kHz 采样率（语音识别最佳）
  -ac 1 \                  # 单声道（语音不需要立体声）
  -b:a 64k \               # 64kbps 码率（语音足够清晰）
  output.mp3
```

```
为什么选这些参数？

  参数          选择          理由
  ─────────────────────────────────────────────────────
  编码          MP3           体积小（WAV 的 1/10），所有 ASR 都支持
  采样率        16kHz         语音频率上限 ~8kHz，16kHz 采样满足奈奎斯特
  声道          单声道         ASR 不需要空间信息，减半体积
  码率          64kbps        人声保真足够，进一步压缩体积
  ─────────────────────────────────────────────────────
  
  效果：2.5 GB 视频 → ~30 MB 音频，体积缩减 99%
```

**Python 实现：**

```python
"""FFmpeg 音频提取"""
import logging
import os
import subprocess

logger = logging.getLogger(__name__)

def extract_audio(video_path: str, audio_path: str) -> str:
    """从视频中提取音频（16kHz mono MP3，适合语音识别）"""
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                   # 去掉视频流
        "-acodec", "libmp3lame", # MP3 编码
        "-ar", "16000",          # 16kHz 采样率
        "-ac", "1",              # 单声道
        "-b:a", "64k",           # 64kbps 码率
        audio_path,
    ]
    logger.info(f"Extracting audio: {video_path} → {audio_path}")
    subprocess.run(cmd, check=True, capture_output=True)
    
    file_size_mb = os.path.getsize(audio_path) / 1024 / 1024
    logger.info(f"Audio extracted: {audio_path} ({file_size_mb:.1f} MB)")
    return audio_path
```

| 参数组合 | 输出体积（3h 视频） | ASR 兼容性 | 音质评价 |
|:---|:---|:---|:---|
| WAV 16kHz mono | ~350 MB | ✅ 全部 | 无损 |
| MP3 16kHz 64k | ~30 MB | ✅ 全部 | 语音清晰 |
| MP3 16kHz 32k | ~15 MB | ✅ 全部 | 略有压缩感 |
| OGG 16kHz 48k | ~22 MB | ⚠️ 部分 | 音质好但兼容差 |

> 💡 **生产建议**：坚持用 MP3 16kHz 64kbps。WAV 体积太大（上传慢），OGG 部分云端 ASR 不支持，低于 64kbps 的 MP3 在嘈杂直播环境下会影响转录准确率。

### 2.2 浏览器端提取：FFmpeg.wasm 与 WORKERFS 零拷贝方案

后端提取音频没什么难度——但如果你要做纯 Web 应用，不让用户上传 2.5 GB 的视频到服务器（太慢），而是在浏览器本地完成音频提取，事情就有意思了。

```
浏览器端音频提取的核心挑战：

  问题 1：FFmpeg 是 C 写的，浏览器只能跑 JS
  ═══════════════════════════════════════
  解决：FFmpeg.wasm — 将 FFmpeg 编译为 WebAssembly
  
  问题 2：2.5 GB 视频读入 WASM 内存会 OOM
  ═══════════════════════════════════════
  解决：WORKERFS — Emscripten 虚拟文件系统
        File handle 惰性读取，不复制整个文件到内存
  
  问题 3：FFmpeg 运行时阻塞主线程
  ═══════════════════════════════════════
  解决：Web Worker 中运行，主线程只接收进度回调
```

**WORKERFS vs writeFile 的内存对比：**

```
旧方案（writeFile）：

  用户选择 2.5 GB 视频
       │
       ▼
  fetchFile() 读取为 Uint8Array     → 占用 2.5 GB
       │
       ▼
  writeFile() 写入 WASM FS          → 再占用 2.5 GB
       │
       ▼
  总内存占用：~5 GB → 直接 OOM 💥


新方案（WORKERFS）：

  用户选择 2.5 GB 视频
       │
       ▼
  mount('WORKERFS', {files: [file]})  → 只保存 File handle
       │
       ▼
  FFmpeg 按需读取字节区间              → 占用 ~50 MB 缓冲区
       │
       ▼
  总内存占用：~50 MB → 4 GB+ 视频也能处理 ✅
```

**TypeScript 实现：**

```typescript
import { FFmpeg } from '@ffmpeg/ffmpeg';

/**
 * WORKERFS 挂载：零拷贝，惰性读取
 * File 对象不会被整体读入内存，FFmpeg 按需读取字节区间
 */
async function mountWorkerFile(
  ffmpeg: FFmpeg,
  file: File,
  mountPoint: string,
): Promise<string> {
  // 创建挂载目录
  try { await ffmpeg.createDir(mountPoint); } catch { /* 已存在 */ }
  
  // WORKERFS 挂载：引用 File handle，不复制数据
  await ffmpeg.mount('WORKERFS', { files: [file] }, mountPoint);
  
  // 返回 WASM 内的虚拟路径
  return `${mountPoint}/${file.name}`;
}

/**
 * 浏览器端音频提取
 */
async function extractAudioInBrowser(
  videoFile: File,
  onProgress?: (ratio: number, message: string) => void,
): Promise<Blob> {
  const ffmpeg = new FFmpeg();
  
  // 1. 加载 FFmpeg.wasm（~30 MB，首次下载后浏览器缓存）
  onProgress?.(0.05, '正在加载音频引擎...');
  await ffmpeg.load({
    coreURL: '/ffmpeg/ffmpeg-core.js',
    wasmURL: '/ffmpeg/ffmpeg-core.wasm',
  });
  
  // 2. 监听进度
  ffmpeg.on('progress', ({ progress }) => {
    onProgress?.(0.1 + progress * 0.85, 
      `正在提取音频... ${Math.round(progress * 100)}%`);
  });
  
  // 3. WORKERFS 挂载（零拷贝）
  const inputPath = await mountWorkerFile(ffmpeg, videoFile, '/input');
  
  // 4. 提取音频（参数与后端完全一致）
  await ffmpeg.exec([
    '-i', inputPath,
    '-vn',                   // 去掉视频
    '-acodec', 'libmp3lame', // MP3 编码
    '-ar', '16000',          // 16kHz
    '-ac', '1',              // 单声道
    '-b:a', '64k',           // 64kbps
    '/output.mp3',
  ]);
  
  // 5. 读取输出（MP3 ~30 MB，内存中没问题）
  const data = await ffmpeg.readFile('/output.mp3', 'binary');
  
  // 6. 清理
  await ffmpeg.unmount('/input');
  await ffmpeg.deleteFile('/output.mp3');
  
  return new Blob([data], { type: 'audio/mpeg' });
}
```

| 方案 | 最大文件 | 内存占用 | 速度 |
|:---|:---|:---|:---|
| `writeFile`（旧） | ~1 GB | 文件大小 × 2 | 慢（全量复制） |
| `WORKERFS`（新） | 4 GB+ | ~50 MB 固定 | 快（惰性读取） |
| 后端 FFmpeg | 无限制 | 极低 | 最快 |

> 💡 **WORKERFS 的限制**：它依赖 Emscripten 的 `SharedArrayBuffer`，需要响应头 `Cross-Origin-Opener-Policy: same-origin` 和 `Cross-Origin-Embedder-Policy: require-corp`。如果你的 CDN 或 Nginx 没配这两个头，WORKERFS 会静默失败。
### 2.3 视频元数据探测与 PTS 偏移修正

这是一个容易被忽略但会导致严重 bug 的问题：**OBS 分段录制的视频，时间戳不是从 0 开始的**。

```
OBS 分段录制的 PTS 偏移问题：

  OBS 录制 3 小时直播，配置每 30 分钟分段：
  
  文件 1：part_001.mp4  (00:00:00 ~ 00:30:00)  start_time = 0
  文件 2：part_002.mp4  (00:30:00 ~ 01:00:00)  start_time = 1800  ← ！
  文件 3：part_003.mp4  (01:00:00 ~ 01:30:00)  start_time = 3600  ← ！
  
  当用户上传 part_003.mp4 时：
  ═══════════════════════════════════════
  • 视频内部的 PTS（Presentation Timestamp）从 3600 秒开始
  • FFmpeg 提取的音频，时间线也从 3600 秒开始
  • Whisper 转录这段音频，输出的时间是相对音频起点的（从 0 开始）
  • 但用户在剪映中打开原视频，时间线显示的是 01:00:00 开始
  
  如果不修正这个偏移：
  ────────────────────────────────────
  Whisper 说 "精彩片段在 00:05:30"
  实际上在原视频的 01:05:30 位置
  用 FFmpeg 按 00:05:30 切片 → 切错位置 💥
```

**探测 PTS 偏移（浏览器端）：**

```typescript
// 用 FFmpeg.wasm 探测视频的 start_time
async function detectStartOffset(
  ffmpeg: FFmpeg,
  inputPath: string,
): Promise<{ startOffset: number; duration: number | null }> {
  const logLines: string[] = [];
  
  // 监听 FFmpeg 日志
  const logHandler = ({ message }: { message: string }) => {
    logLines.push(message);
  };
  ffmpeg.on('log', logHandler);
  
  try {
    // 只读极短一段来获取文件信息（几乎瞬间完成）
    await ffmpeg.exec([
      '-i', inputPath, '-t', '0.01', '-f', 'null', '-'
    ]);
  } catch {
    // 即使 exec 报错，log 中已包含文件信息
  }
  ffmpeg.off('log', logHandler);
  
  let startOffset = 0;
  let duration: number | null = null;
  
  for (const line of logLines) {
    // 解析时长：Duration: 01:30:00.00
    const durationMatch = line.match(/Duration:\s+(\d+):(\d+):([\d.]+)/);
    if (durationMatch && duration === null) {
      duration = parseInt(durationMatch[1]) * 3600 
               + parseInt(durationMatch[2]) * 60 
               + parseFloat(durationMatch[3]);
    }
    
    // 解析起始偏移：start: 3600.000000
    const startMatch = line.match(/start:\s+([\d.]+)/);
    if (startMatch) {
      const parsed = parseFloat(startMatch[1]);
      if (parsed > 1) {  // 忽略 <1s 的编码延迟
        startOffset = parsed;
      }
      break;
    }
  }
  
  return { startOffset, duration };
}
```

**后端修正偏移（应用到转录结果）：**

```python
# 在转录完成后，将 PTS 偏移加回到所有时间戳上
start_offset = getattr(task, 'video_start_offset', 0.0) or 0.0

if start_offset > 1.0:
    logger.info(f"应用视频 PTS 偏移 {start_offset:.1f}s")
    for seg in transcript:
        seg["start"] += start_offset
        seg["end"] += start_offset
```

```
修正后的时间线对齐：

  原视频 (part_003.mp4)
  ├── PTS 起点: 3600s (01:00:00)
  ├── 视频时长: 1800s (30 分钟)
  └── PTS 终点: 5400s (01:30:00)

  Whisper 转录结果（修正前）
  ├── segment[0]: start=0.0, end=5.2, text="大家好..."
  └── segment[N]: start=1795.0, end=1800.0, text="下播了..."

  Whisper 转录结果（加上 3600s 偏移后）
  ├── segment[0]: start=3600.0, end=3605.2, text="大家好..."
  └── segment[N]: start=5395.0, end=5400.0, text="下播了..."
  
  ✅ 现在用 FFmpeg -ss 3600 切视频，时间点完全对齐
```

> 💡 **何时需要修正**：只有 OBS 分段录制（或类似的连续录制分段工具）才会产生非零 `start_time`。直接用手机录制或单文件录制的视频，`start_time` 通常是 0，不需要修正。代码中用 `> 1.0` 的阈值过滤掉编码产生的微小偏移。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **音频提取参数** | MP3 16kHz mono 64kbps，2.5 GB 视频 → 30 MB 音频 |
| **FFmpeg.wasm** | FFmpeg 的 WebAssembly 版本，让浏览器能处理音视频 |
| **WORKERFS** | 零拷贝挂载 File handle，解决大文件 OOM，内存占用 ~50 MB |
| **PTS 偏移** | OBS 分段录制的视频时间戳不从 0 开始，必须探测并修正 |
| **前后端一致** | 浏览器端和后端的提取参数必须完全一致（同编码、同采样率） |

---

## 3. 第二层：语音转录（ASR）

音频提取完成后，下一步是把语音信号转换成带时间戳的文本。这一层是整条管线中**耗时最长**的环节（占总耗时 60-80%），也是成本差异最大的环节——本地 GPU 免费但需要硬件，云端 API 按时长收费但开箱即用。本章实现三种方案并让系统自动选择。

### 3.1 本地 GPU 方案：faster-whisper + CUDA

如果你的服务器有 NVIDIA GPU（哪怕是 RTX 3060），本地跑 Whisper 就是最优选——免费、精准、数据不出服务器。

`faster-whisper` 是 Whisper 的 CTranslate2 优化版，速度比原版快 4 倍，显存占用减半：

```python
"""GPU 环境：faster-whisper 本地转录"""
from faster_whisper import WhisperModel

class LocalWhisperTranscriber:
    """CUDA GPU 本地转录"""
    
    def __init__(self):
        self.model = WhisperModel(
            "large-v3",          # 最大最准的模型
            device="cuda",       # 使用 GPU
            compute_type="float16",  # 半精度，速度翻倍
        )
    
    async def transcribe(self, audio_path: str) -> list[dict]:
        segments, info = self.model.transcribe(
            audio_path,
            language="zh",       # 指定中文（比自动检测快且准）
            vad_filter=True,     # VAD 过滤静音段
            vad_parameters={
                "min_silence_duration_ms": 500,  # 500ms 以上静音才切分
            },
            word_timestamps=True,  # 词级别时间戳
        )
        
        result = []
        for seg in segments:
            result.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
        
        return result
```

```
faster-whisper 关键参数说明：

  参数                    选择              理由
  ─────────────────────────────────────────────────────
  model_size              large-v3          中文 WER ~4%，精度最高
  compute_type            float16           速度翻倍，精度几乎无损
  language                "zh"              跳过语言检测，提速 10%
  vad_filter              True              过滤静音段，减少幻觉
  min_silence_duration_ms 500               直播语速快，500ms 比默认 2s 更合适
  word_timestamps         True              支持精确到词的时间点
  ─────────────────────────────────────────────────────
```

| GPU | 3h 音频转录耗时 | 显存占用 | 实时倍率 |
|:---|:---|:---|:---|
| RTX 4090 | ~3 分钟 | ~3.5 GB | ~60x |
| RTX 3060 | ~8 分钟 | ~3.5 GB | ~22x |
| RTX 3060 (int8) | ~6 分钟 | ~2.0 GB | ~30x |
| A100 80GB | ~2 分钟 | ~3.5 GB | ~90x |

> 💡 **VAD 的重要性**：直播录像中有大量静音（暂离、放音乐、等弹幕）。开启 `vad_filter` 后，Whisper 只处理有人声的段落，速度提升 30-50%，同时避免在静音段产生"幻觉文本"（Whisper 的已知问题——在无人声时会编造内容）。

### 3.2 Apple Silicon 方案：mlx-whisper 本地加速

如果你在 Mac（M1/M2/M3）上开发，没有 NVIDIA GPU，`mlx-whisper` 是最好的替代——利用 Apple 的 MLX 框架在 Metal GPU 上加速推理：

::: v-pre
```python
"""Apple Silicon Mac：mlx-whisper 本地转录"""
import asyncio
import json
import os
import sys

class MLXWhisperTranscriber:
    """Apple Silicon Mac 本地转录"""
    
    def __init__(self, model: str = "mlx-community/whisper-large-v3-turbo"):
        self.model = model
    
    async def transcribe(self, audio_path: str) -> list[dict]:
        """子进程执行（MLX Metal 后端不能在子线程中工作）"""
        import tempfile
        output_file = tempfile.mktemp(suffix=".json")
        
        # MLX Metal 只能在主线程运行，必须用独立进程
        script = f"""
import json
import mlx_whisper

output = mlx_whisper.transcribe(
    "{audio_path}",
    path_or_hf_repo="{self.model}",
    language="zh",
    word_timestamps=True,
    verbose=True,
)

segments = []
for seg in output.get("segments", []):
    text = seg.get("text", "").strip()
    if not text:
        continue
    segments.append(&#123;&#123;
        "start": seg.get("start", 0.0),
        "end": seg.get("end", 0.0),
        "text": text,
    &#125;&#125;)

with open("{output_file}", "w") as f:
    json.dump(segments, f, ensure_ascii=False)
"""
        # 用当前 venv 的 Python 执行
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-c", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"MLX Whisper 失败: {stderr.decode()[:300]}")
        
        with open(output_file, "r") as f:
            result = json.load(f)
        os.remove(output_file)
        
        return result
```
:::

```
为什么 MLX Whisper 要用子进程？

  MLX 框架的 Metal 后端有一个限制：
  ═══════════════════════════════════════
  Metal GPU 操作必须在主线程执行。
  
  但我们的 FastAPI 应用运行在 asyncio 事件循环中，
  ARQ Worker 在子线程里执行任务。
  
  如果直接在 Worker 线程中调用 mlx_whisper.transcribe()：
  → Metal 初始化失败
  → 静默回退到 CPU（慢 10 倍）
  → 或直接 crash
  
  解决方案：
  ════════════════════════════
  用 asyncio.create_subprocess_exec() 启动独立进程
  独立进程的主线程 = Metal 可以正常工作
  结果通过临时 JSON 文件传回
```

| 芯片 | 3h 音频转录耗时 | 内存占用 | 实时倍率 |
|:---|:---|:---|:---|
| M1 Pro | ~15 分钟 | ~4 GB | ~12x |
| M2 Max | ~10 分钟 | ~4 GB | ~18x |
| M3 Max | ~8 分钟 | ~4 GB | ~22x |

> 💡 **turbo vs large-v3**：`whisper-large-v3-turbo` 是 large-v3 的蒸馏版，速度快 2-3 倍，中文 WER 从 ~4% 上升到 ~5%，对于直播切片这种不需要逐字精确的场景完全够用。优先用 turbo。

### 3.3 云端方案：阿里云 Flash Recognizer

没有 GPU（CUDA 或 Apple Silicon 都没有）？云端 ASR 是兜底方案。阿里云的 Flash Recognizer 是国内性价比最高的选择——支持 60 分钟以内的音频一次性识别，中文准确率高。

```python
"""无 GPU 环境：阿里云 Flash Recognizer"""
import httpx
import logging

logger = logging.getLogger(__name__)

class AliyunASRTranscriber:
    """阿里云 Flash ASR 云端转录"""
    
    SUBMIT_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/FlashRecognizer"
    
    def __init__(self, appkey: str, token: str):
        self.appkey = appkey
        self.token = token
    
    async def _transcribe_single(self, audio_path: str) -> list[dict]:
        """转录单个音频文件（≤60 分钟）"""
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        format_type = "mp3" if audio_path.endswith(".mp3") else "wav"
        
        params = {
            "appkey": self.appkey,
            "token": self.token,
            "format": format_type,
            "sample_rate": 16000,
            "enable_words": "true",  # 返回词级别时间戳
        }
        
        # 直接 POST 音频二进制数据
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, read=600.0)
        ) as client:
            response = await client.post(
                self.SUBMIT_URL,
                params=params,
                content=audio_data,
                headers={"Content-Type": "application/octet-stream"},
            )
        
        data = response.json()
        if data.get("status") != 20000000:
            raise RuntimeError(f"ASR 错误: {data.get('message')}")
        
        # 解析结果
        result = []
        sentences = data.get("flash_result", {}).get("sentences", [])
        for sent in sentences:
            text = sent.get("text", "").strip()
            if not text:
                continue
            result.append({
                "start": sent.get("begin_time", 0) / 1000.0,   # 毫秒 → 秒
                "end": (sent["begin_time"] + sent["duration"]) / 1000.0,
                "text": text,
            })
        
        return result
```

```
阿里云 Flash ASR 的关键注意点：

  1. Token 获取
  ═══════════════════════════════════════
  • 方式 A：控制台手动创建 Token（有效期 24 小时）
  • 方式 B：AK/SK 动态获取（推荐，自动续期）
  • Token 过期后请求会返回 40000000 错误
  
  2. 时间单位转换
  ═══════════════════════════════════════
  • 阿里云返回的时间单位是毫秒（begin_time=5230）
  • 我们的管线统一用秒（start=5.23）
  • 必须做 / 1000.0 转换，否则时间轴全乱
  
  3. 文件大小限制
  ═══════════════════════════════════════
  • Flash Recognizer 单次最大 512 MB / 60 分钟
  • 超过需要切分（见 3.4 节）
```

| 对比维度 | faster-whisper (GPU) | mlx-whisper (Mac) | 阿里云 Flash ASR |
|:---|:---|:---|:---|
| **硬件要求** | NVIDIA GPU | Apple Silicon | 无 |
| **成本** | 免费 | 免费 | ~0.8 元/小时 |
| **3h 音频耗时** | 3-8 分钟 | 8-15 分钟 | 1-2 分钟 |
| **中文准确率** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **数据隐私** | ✅ 本地 | ✅ 本地 | ❌ 上传云端 |
| **长音频** | 无限制 | 无限制 | ≤60 分钟/次 |

> 💡 **选型决策**：有 GPU 用 faster-whisper，Mac 开发用 mlx-whisper，两者都没有才用阿里云。核心考量不是准确率（三者差距 <2%），而是成本和隐私。
### 3.4 长音频自动切分与时间偏移合并

云端 ASR 有时长限制（阿里云 Flash ≤ 60 分钟），3 小时的直播音频必须切分后逐段转录再合并。关键难点是**时间偏移修正**——每段切分后的转录时间从 0 开始，必须加回原始偏移量。

```python
"""长音频自动切分与合并"""
import os
import subprocess

MAX_CHUNK_MINUTES = 50  # 每段最大 50 分钟（留 10 分钟安全余量）

def _get_audio_duration(audio_path: str) -> float:
    """用 ffprobe 获取音频时长（秒）"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def split_audio(audio_path: str, chunk_seconds: int) -> list[tuple[str, float]]:
    """
    FFmpeg 切分长音频。
    
    Returns:
        [(chunk_path, offset_seconds), ...] — 每段路径和起始偏移
    """
    duration = _get_audio_duration(audio_path)
    if duration <= chunk_seconds:
        return [(audio_path, 0.0)]  # 不需要切分
    
    base, ext = os.path.splitext(audio_path)
    chunks = []
    start = 0.0
    
    while start < duration:
        chunk_idx = len(chunks)
        chunk_path = f"{base}_chunk{chunk_idx:03d}{ext}"
        end = min(start + chunk_seconds, duration)
        
        # 流拷贝（-c copy），几乎瞬间完成
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start), "-to", str(end),
            "-i", audio_path,
            "-c", "copy",
            chunk_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        chunks.append((chunk_path, start))
        start = end
    
    return chunks
```

```
长音频切分与合并的时间线：

  原始音频：3 小时 (10800 秒)
  ═══════════════════════════════════════════
  
  切分为 4 段（每段 50 分钟 = 3000 秒）：
  
  Chunk 0: 0s ~ 3000s      offset = 0
  Chunk 1: 3000s ~ 6000s    offset = 3000
  Chunk 2: 6000s ~ 9000s    offset = 6000
  Chunk 3: 9000s ~ 10800s   offset = 9000
  
  每段转录后的时间修正：
  ────────────────────────────────────
  Chunk 1 转录结果: start=5.2, end=8.7, text="..."
  加上 offset 3000: start=3005.2, end=3008.7, text="..."
  
  最终按 start 排序合并所有段 → 完整时间线
```

**合并逻辑：**

```python
async def transcribe_long_audio(
    transcriber,  # _transcribe_single 方法
    audio_path: str,
) -> list[dict]:
    """自动切分 + 逐段转录 + 时间修正 + 合并"""
    chunk_seconds = MAX_CHUNK_MINUTES * 60
    chunks = split_audio(audio_path, chunk_seconds)
    
    all_segments = []
    for i, (chunk_path, offset) in enumerate(chunks):
        # 转录单段
        segments = await transcriber(chunk_path)
        
        # 修正时间偏移
        for seg in segments:
            seg["start"] += offset
            seg["end"] += offset
        
        all_segments.extend(segments)
        
        # 清理临时切分文件
        if chunk_path != audio_path:
            os.remove(chunk_path)
    
    # 按时间排序
    all_segments.sort(key=lambda x: x["start"])
    return all_segments
```

> 💡 **切分用 `-c copy`（流拷贝）**：不要用重编码切分，流拷贝只是在字节流上做切割，3 小时音频的切分在 1 秒内完成。重编码切分会额外花几十秒，而且可能引入微小的时间偏移。
### 3.5 环境自适应：工厂模式自动选择转录器

三种转录方案都有了，最后一步是让系统**自动检测运行环境**，选择最优方案。这里用经典的工厂模式：

```python
"""根据运行环境自动选择转录方案"""
from abc import ABC, abstractmethod

class BaseTranscriber(ABC):
    """转录器基类：统一接口"""
    
    @abstractmethod
    async def transcribe(self, audio_path: str) -> list[dict]:
        """
        转录音频，返回带时间戳的文本段落。
        Returns: [{"start": float, "end": float, "text": str}, ...]
        """
        ...

def get_transcriber() -> BaseTranscriber:
    """根据运行环境自动选择转录方案
    
    优先级：CUDA GPU → MLX (Apple Silicon) → 阿里云 ASR
    """
    # 1. CUDA GPU（Linux/Windows 服务器）
    try:
        import torch
        if torch.cuda.is_available():
            logger.info("CUDA available → LocalWhisperTranscriber")
            return LocalWhisperTranscriber()
    except ImportError:
        pass
    
    # 2. Apple Silicon Mac（MLX 加速）
    try:
        import mlx_whisper  # noqa: F401
        logger.info("mlx-whisper available → MLXWhisperTranscriber")
        return MLXWhisperTranscriber()
    except ImportError:
        pass
    
    # 3. 兜底：阿里云 ASR
    logger.info("No local model → AliyunASRTranscriber")
    return AliyunASRTranscriber()
```

```
工厂模式的自动选择逻辑：

  部署环境                      自动选择
  ═══════════════════════════════════════════
  Linux + NVIDIA GPU            faster-whisper (CUDA)
  macOS + M1/M2/M3              mlx-whisper (Metal)
  Linux / Windows 无 GPU        阿里云 Flash ASR
  Docker 容器 (无 GPU)          阿里云 Flash ASR
  ═══════════════════════════════════════════
  
  优势：
  • 同一套代码部署到任何环境都能工作
  • 开发在 Mac 上用 mlx-whisper（免费）
  • 生产在 GPU 服务器用 faster-whisper（免费 + 最快）
  • 轻量部署在无 GPU 云服务器上用阿里云（最便宜的云方案）
```

这种设计让管线代码完全不需要关心底层用的是哪个转录器——只需要调用 `get_transcriber().transcribe(audio_path)`，剩下的由工厂自动处理。

> 💡 **检测顺序很重要**：先检测 CUDA 再检测 MLX，因为理论上可能存在同时安装了 torch 和 mlx_whisper 的环境（比如在 Mac 上装了 torch CPU 版）。CUDA 优先是因为它的 faster-whisper 速度最快。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **faster-whisper** | CTranslate2 优化版 Whisper，速度 4x，显存减半，生产首选 |
| **mlx-whisper** | Apple Silicon 本地转录，必须用子进程（Metal 主线程限制） |
| **阿里云 Flash** | 云端兜底方案，注意时间单位 ms→s 转换和 60 分钟时长限制 |
| **长音频切分** | FFmpeg `-c copy` 流拷贝切分 + 时间偏移合并，瞬间完成 |
| **工厂模式** | 自动检测 CUDA → MLX → 云端，一套代码适配所有环境 |
| **VAD 过滤** | 过滤静音段，提速 30-50%，同时消除 Whisper 幻觉问题 |

---

## 4. 第三层：LLM 语义分析

转录完成后，你手里有了一份几万字的带时间戳文本。下一步是让 LLM 从中找出"值得做成短视频的精彩片段"。这一层的挑战不在调 API——而在于如何让 LLM 稳定、准确、可靠地输出**结构化的切片方案**。

### 4.1 转录文本分批：Token 预算与上下文切分

3 小时直播的转录文本可能有 3-5 万字。即使现代 LLM 支持 128K 上下文，一次性塞进去也不是好主意——Token 成本高、响应慢、而且精度会随上下文长度下降。

```
为什么要分批？

  3h 直播转录文本 ≈ 40,000 字
  ═══════════════════════════════════════
  40,000 中文字 ≈ 27,000 Token（中文约 1.5 字/Token）
  
  问题 1：成本
  ────────────────────────────────────
  DeepSeek V3：输入 ¥1/M Token → 27K Token ≈ ¥0.027
  但如果用 GPT-4o：输入 $2.5/M Token → 27K Token ≈ ¥0.5
  分批可以只对有内容的段落调用，跳过闲聊/静音
  
  问题 2：精度
  ────────────────────────────────────
  LLM 的 "Lost in the Middle" 问题：
  超长文本中，中间部分的信息容易被忽略
  分成 5-6 批，每批 6000 Token，精度更高
  
  问题 3：可靠性
  ────────────────────────────────────
  一次调用失败 = 全部重来
  分批后单批失败只丢失部分结果，其余不受影响
```

**分批实现：**

```python
class ClipAnalyzer:
    """直播切片分析器"""
    
    MAX_TOKENS_PER_BATCH = 6000  # 每批约 6000 Token
    
    def _split_transcript(self, transcript: list[dict]) -> list[list[dict]]:
        """按 Token 预算分批"""
        batches, current_batch, current_tokens = [], [], 0
        
        for seg in transcript:
            # 中文约 1.5 字符 = 1 Token
            seg_tokens = len(seg["text"]) / 1.5
            
            if current_tokens + seg_tokens > self.MAX_TOKENS_PER_BATCH \
               and current_batch:
                batches.append(current_batch)
                current_batch, current_tokens = [], 0
            
            current_batch.append(seg)
            current_tokens += seg_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _format_transcript(self, segments: list[dict]) -> str:
        """格式化为带时间轴的文本"""
        lines = []
        for seg in segments:
            start = self._format_time(seg["start"])
            end = self._format_time(seg["end"])
            lines.append(f"[{start} → {end}] {seg['text']}")
        return "\n".join(lines)
```

> 💡 **6000 Token 的依据**：这个数字保证每批转录文本约 9000 字（~15 分钟内容），LLM 能完整阅读不遗漏，同时留足输出空间（通常每批输出 1000-2000 Token）。

### 4.2 Prompt 设计：让 LLM 当"剪辑师"

Prompt 设计是这一层最关键的环节。一个好的 Prompt 需要做到四件事：定义角色、给出标准、约束格式、提供示例。

::: v-pre
```python
CLIP_ANALYSIS_PROMPT = """你是一个直播切片剪辑专家。分析以下直播转录文本，\
找出适合制作短视频切片的精彩片段。

## 转录文本（带时间轴）
{transcript}

## 切片标准
1. **高能时刻**：情绪爆发、搞笑片段、争议讨论
2. **干货知识**：有价值的观点、教程、经验分享
3. **互动精彩**：与观众的精彩互动
4. **金句名言**：可传播的经典语句
5. **带货亮点**：产品展示、砍价、用户反馈（如适用）

## 切片要求
- 每个切片 30秒 ~ 3分钟
- 片段要有完整的起承转合，不能话说一半就切
- 开头要有"钩子"（吸引注意力的内容）
- 结尾要有"价值感"（学到东西、被逗笑、有共鸣）

## 输出格式
请严格输出 JSON 数组，不要包含其他文本：
[
  &#123;&#123;
    "clip_id": 1,
    "title": "切片标题（吸引眼球）",
    "start_time": 750.0,
    "end_time": 885.0,
    "duration": 135.0,
    "type": "高能时刻",
    "summary": "内容概要",
    "virality_score": 8,
    "suggested_caption": "推荐的发布文案"
  &#125;&#125;
]"""
```
:::

```
Prompt 设计的四层结构：

  第 1 层：角色定义
  ═══════════════════════════════════════
  "你是一个直播切片剪辑专家"
  → 激活 LLM 中与"视频剪辑"相关的知识权重
  
  第 2 层：切片标准（领域知识注入）
  ═══════════════════════════════════════
  高能时刻 / 干货知识 / 互动精彩 / 金句 / 带货
  → 告诉 LLM "什么算精彩"，避免它按自己的标准乱选
  
  第 3 层：约束条件
  ═══════════════════════════════════════
  30s ~ 3min / 完整起承转合 / 有钩子 / 有价值感
  → 控制输出质量，避免切出 5 秒的碎片或 10 分钟的长段
  
  第 4 层：输出格式（JSON Schema）
  ═══════════════════════════════════════
  严格的 JSON 数组 + 字段定义
  → 机器可解析，不需要人工提取
```

| Prompt 技巧 | 作用 | 示例 |
|:---|:---|:---|
| **角色定义** | 引导模型进入专业模式 | "你是直播切片剪辑专家" |
| **评分维度** | 提供量化标准 | `virality_score: 1-10` |
| **负面约束** | 避免常见错误 | "不能话说一半就切" |
| **格式强制** | 确保输出可解析 | "严格输出 JSON 数组" |
| **示例 JSON** | 消除格式歧义 | 完整的输出样例 |

> 💡 **`temperature=0.3` 的选择**：切片分析需要稳定性（同一段文本每次分析结果应该接近），但也需要一定创造性（标题和文案要吸引人）。0.3 是平衡点——比 0 多一些创意，比 0.7 少很多随机性。

### 4.3 LLM 响应解析：从非结构化文本到可靠 JSON

即使你在 Prompt 里写了"严格输出 JSON"，LLM 依然会各种花式违规。你必须实现**多层容错解析**：

```
LLM 常见的输出"惊喜"：

  情况 1：正常 JSON ✅
  ═══════════════════════════════════════
  [{"clip_id": 1, "title": "...", ...}]
  
  情况 2：Markdown 代码块包裹 ⚠️
  ═══════════════════════════════════════
  ```json
  [{"clip_id": 1, "title": "...", ...}]
  ```
  
  情况 3：前后加了废话 ⚠️
  ═══════════════════════════════════════
  以下是我分析出的精彩片段：
  [{"clip_id": 1, ...}]
  以上就是我的分析。
  
  情况 4：返回空内容 ❌
  ═══════════════════════════════════════
  （空字符串或无意义的回复）
  
  情况 5：JSON 格式错误 ❌
  ═══════════════════════════════════════
  [{"clip_id": 1, "title": "标题里有"引号"导致解析失败"}]
```

**多层容错解析实现：**

```python
import json
import re

def parse_llm_response(content: str) -> list[dict]:
    """多层容错解析 LLM 返回的 JSON"""
    content = content.strip()
    
    # 第 1 层：去掉 Markdown 代码块包裹
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    
    # 第 2 层：直接尝试解析
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    
    # 第 3 层：正则提取 JSON 数组部分
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            logger.error(f"Found JSON-like array but parse failed")
    
    # 全部失败
    logger.error(f"Cannot parse LLM response: {content[:500]}")
    return []
```

**带重试的分析调用：**

```python
MAX_RETRIES = 3

async def _analyze_batch_with_retry(
    self, batch_idx: int, total: int, batch: list[dict]
) -> list[dict] | None:
    """带重试的单批次分析"""
    formatted = self._format_transcript(batch)
    prompt = CLIP_ANALYSIS_PROMPT.format(transcript=formatted)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=120,
            )
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                await asyncio.sleep(2 * attempt)
                continue
            
            clips = parse_llm_response(content)
            if clips:
                return clips
            
            # 解析出空数组 → 重试
            await asyncio.sleep(2 * attempt)
            
        except Exception as e:
            logger.error(f"Batch {batch_idx+1} attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(3 * attempt)
    
    return None  # 彻底失败
```

```
重试策略：

  Attempt 1 → 失败 → 等 2 秒
  Attempt 2 → 失败 → 等 4 秒
  Attempt 3 → 失败 → 放弃该批次，继续处理其他批次
  
  关键设计：
  ═══════════════════════════════════════
  • 单批失败不影响其他批次（部分成功优先）
  • 指数退避（2s → 4s → 6s）避免 API 限流
  • 超时设置 120 秒（长文本分析可能需要较长时间）
  • 返回 None 表示彻底失败，由上层记录并继续
```

> 💡 **"部分成功"vs"全有全无"**：5 批分析中 1 批失败，你仍然拿到了 80% 的结果。这比因为 1 批失败就丢掉全部好得多——用户看到"找到 8 个精彩片段"比"分析失败"有价值得多。
### 4.4 结果去重与排序：时间重叠检测算法

分批分析会产生一个问题——相邻批次的边界区域可能被两批都识别为精彩片段，导致重复。需要用时间重叠检测来去重。

```
重叠去重的原理：

  Batch 1 输出的 Clip A: [300s ~ 420s] ⭐ score=8
  Batch 2 输出的 Clip B: [310s ~ 430s] ⭐ score=7
  
  重叠区间: [310s ~ 420s] = 110 秒
  Clip A 时长: 120 秒
  重叠占比: 110/120 = 91.7% > 50%
  
  → Clip A 和 B 高度重叠
  → 保留 score 更高的 Clip A，丢弃 Clip B
```

**去重实现：**

```python
def _deduplicate(self, clips: list[dict]) -> list[dict]:
    """去重：时间段重叠超过 50% 的保留高分项"""
    if not clips:
        return clips
    
    # 先按 virality_score 降序排列（高分优先保留）
    clips.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
    
    result = [clips[0]]  # 最高分的一定保留
    
    for clip in clips[1:]:
        overlap = False
        for existing in result:
            # 计算重叠区间
            overlap_start = max(clip["start_time"], existing["start_time"])
            overlap_end = min(clip["end_time"], existing["end_time"])
            
            if overlap_end > overlap_start:
                overlap_duration = overlap_end - overlap_start
                clip_duration = clip["end_time"] - clip["start_time"]
                
                # 重叠超过 50% → 视为重复
                if overlap_duration / clip_duration > 0.5:
                    overlap = True
                    break
        
        if not overlap:
            result.append(clip)
    
    return result
```

```
完整的分析流程（汇总）：

  转录文本 (N 段)
       │
       ▼ _split_transcript()
  分成 K 批（每批 ≤ 6000 Token）
       │
       ▼ _analyze_batch_with_retry() × K
  每批独立调用 LLM，带 3 次重试
       │
       ▼ parse_llm_response()
  多层容错解析 JSON
       │
       ▼ 合并所有批次结果
  更新 clip_id 为全局连续编号
       │
       ▼ _deduplicate()
  按 virality_score 降序，50% 重叠阈值去重
       │
       ▼
  最终切片方案: [{clip_id, title, start_time, end_time, ...}, ...]
```

> 💡 **50% 重叠阈值的选择**：太低（如 20%）会误杀"时间接近但内容不同"的片段；太高（如 80%）会漏掉"几乎相同但时间微偏"的重复。50% 在实际测试中平衡性最好。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Token 分批** | 每批 6000 Token，避免"Lost in the Middle"精度下降 |
| **Prompt 四层** | 角色定义 → 切片标准 → 约束条件 → 输出格式 |
| **容错解析** | 代码块剥离 → 直接解析 → 正则提取，三层兜底 |
| **重试策略** | 3 次指数退避，单批失败不影响全局（部分成功优先） |
| **重叠去重** | 时间重叠 >50% 的保留高分项，防止批次边界重复 |

---

## 5. 第四层：视频切片与导出

LLM 分析完成后，你拿到了一组切片方案：`[{start_time, end_time, title}, ...]`。下一步是把这些时间点变成真正的视频文件。这一层看似简单——就是调 FFmpeg 切一刀——但关键帧对齐、编码质量、批量容错、浏览器端切片这些问题加在一起，坑不少。

### 5.1 FFmpeg 精确切片：关键帧与重编码的权衡

FFmpeg 切片有两种模式，效果差别很大：

```
两种切片模式的对比：

  模式 1：流拷贝（-c copy）
  ═══════════════════════════════════════
  ffmpeg -ss 300 -to 420 -i input.mp4 -c copy output.mp4
  
  • 速度：极快（几秒）
  • 质量：无损
  • 问题：起止点只能对齐到最近的关键帧（I 帧）
  • 结果：实际切出来可能是 298.5s ~ 421.2s
  • 适合：对精度要求不高的快速预览
  
  模式 2：重编码（-c:v libx264）⭐ 推荐
  ═══════════════════════════════════════
  ffmpeg -ss 300 -to 420 -i input.mp4 \
    -c:v libx264 -c:a aac -preset fast -crf 23 output.mp4
  
  • 速度：慢（每段 10-30 秒）
  • 质量：几乎无损（CRF 23 肉眼看不出区别）
  • 优点：精确到毫秒级别
  • 结果：准确切出 300.000s ~ 420.000s
  • 适合：最终交付的切片（发抖音/快手）
```

**生产级切片实现：**

```python
"""FFmpeg 精确切片"""
import subprocess
import os

def clip_video(
    video_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
) -> str:
    """FFmpeg 精确切片（重编码确保关键帧对齐）"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", _seconds_to_ffmpeg_time(start_time),
        "-to", _seconds_to_ffmpeg_time(end_time),
        "-i", video_path,
        "-c:v", "libx264",   # H.264 编码（兼容性最好）
        "-c:a", "aac",       # AAC 音频
        "-preset", "fast",   # 编码速度 vs 压缩率的平衡
        "-crf", "23",        # 质量级别（18=高质量 23=平衡 28=小文件）
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def _seconds_to_ffmpeg_time(seconds: float) -> str:
    """秒数转 FFmpeg 时间格式 HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"
```

| 参数 | 选择 | 理由 |
|:---|:---|:---|
| `-c:v libx264` | H.264 | 所有平台兼容，硬件解码支持最广 |
| `-preset fast` | fast | 比 medium 快 2 倍，文件只大 5-10% |
| `-crf 23` | 23 | 视觉无损，1080p 2 分钟视频约 30-50 MB |
| `-c:a aac` | AAC | MP4 标准音频编码 |

> 💡 **`-ss` 放在 `-i` 前面 vs 后面**：放前面（input seeking）是粗略定位后再精确解码，速度更快；放后面（output seeking）是从头解码到目标位置，更精确但慢。对于重编码模式，两者精度一样，但放前面快很多。

### 5.2 批量切片：错误隔离与部分成功策略

一次分析可能产出 10-15 个切片方案。批量切片时，一定不能因为某段失败就丢掉全部：

```python
def batch_clip(
    video_path: str,
    clips: list[dict],
    output_dir: str,
) -> list[str]:
    """批量切片，单段失败不影响其他段"""
    os.makedirs(output_dir, exist_ok=True)
    outputs = []
    
    for clip in clips:
        # 生成安全文件名
        safe_title = "".join(
            c for c in clip.get("title", "clip")[:20]
            if c.isalnum() or c in ("_", "-", " ")
        ).strip()
        filename = f"clip_{clip['clip_id']:03d}_{safe_title}.mp4"
        output_path = os.path.join(output_dir, filename)
        
        try:
            clip_video(
                video_path,
                clip["start_time"],
                clip["end_time"],
                output_path,
            )
            outputs.append(output_path)
        except subprocess.CalledProcessError as e:
            # 单段失败 → 记录日志，继续处理下一段
            logger.error(f"Clip {clip['clip_id']} failed: {e}")
            continue
    
    logger.info(f"Batch done: {len(outputs)}/{len(clips)} succeeded")
    return outputs
```

```
部分成功策略：

  10 个切片方案
  ═══════════════════════════════════════
  clip_001 ✅ 成功
  clip_002 ✅ 成功
  clip_003 ❌ 失败（时间点超出视频范围）
  clip_004 ✅ 成功
  ...
  clip_010 ✅ 成功
  
  结果：9/10 成功
  ────────────────────────────────────
  ✅ 返回 9 个切片文件，用户看到 "成功导出 9 段，失败 1 段"
  ❌ 不要因为 1 段失败就全部报错
```

> 💡 **文件名安全处理**：标题可能包含 `/`、`\`、`:`、`"` 等文件系统非法字符。用白名单过滤（只保留字母、数字、下划线、连字符、空格）是最稳妥的做法，同时截断到 20 字符防止路径过长。

### 5.3 浏览器端本地切片：无需回传原视频

在"音频直传"架构中，用户只上传了 30 MB 音频给后端做 AI 分析，2.5 GB 的原视频从未离开用户电脑。那切片怎么办？答案是**在浏览器本地切片**——复用第 2 章的 FFmpeg.wasm + WORKERFS 方案。

```
浏览器端切片的工作流：

  用户电脑                          服务器
  ═══════════════                  ═══════════════
  原视频 (2.5 GB)                  
       │                           
  浏览器提取音频 ────上传 30 MB────▶ AI 分析
       │                           ← 返回切片方案 (5 KB JSON)
       │                           
  浏览器本地切片 ◀── 切片方案 ──────┘
       │
  逐段 FFmpeg.wasm 裁切
       │
  打包 ZIP 下载
  
  关键优势：
  ─────────────────────────────────
  • 2.5 GB 原视频始终在用户电脑，不上传
  • 只上传 30 MB 音频（上传时间从 30 分钟 → 30 秒）
  • 切片在浏览器本地完成，服务器零负载
```

**核心实现：**

```typescript
import { FFmpeg } from '@ffmpeg/ffmpeg';
import { zipSync, strToU8 } from 'fflate';

interface ClipPlan {
  clip_index: number;
  title: string;
  start_time: number;
  end_time: number;
}

async function exportClipsLocally(
  videoFile: File,
  clips: ClipPlan[],
  onProgress?: (current: number, total: number) => void,
): Promise<Blob> {
  const ffmpeg = new FFmpeg();
  await ffmpeg.load({ /* ... */ });
  
  // WORKERFS 挂载原视频
  const inputPath = await mountWorkerFile(ffmpeg, videoFile, '/input');
  
  const zipFiles: Record<string, Uint8Array> = {};
  
  for (let i = 0; i < clips.length; i++) {
    const clip = clips[i];
    onProgress?.(i + 1, clips.length);
    
    const outputName = `/clip_${String(i + 1).padStart(2, '0')}.mp4`;
    
    try {
      // 逐段切片（重编码模式）
      await ffmpeg.exec([
        '-ss', String(clip.start_time),
        '-to', String(clip.end_time),
        '-i', inputPath,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-preset', 'fast',
        '-crf', '23',
        outputName,
      ]);
      
      // 读取切片文件
      const data = await ffmpeg.readFile(outputName, 'binary');
      const safeName = `${String(i + 1).padStart(2, '0')}_${clip.title}.mp4`;
      zipFiles[safeName] = new Uint8Array(data as Uint8Array);
      
      // 清理当前切片（释放 WASM 内存）
      await ffmpeg.deleteFile(outputName);
    } catch (err) {
      console.warn(`Clip ${i + 1} failed, skipping...`, err);
    }
  }
  
  // 打包 ZIP（fflate，纯 JS，快且轻量）
  const zipped = zipSync(zipFiles);
  return new Blob([zipped], { type: 'application/zip' });
}
```

| 对比维度 | 后端切片 | 浏览器端切片 |
|:---|:---|:---|
| **网络传输** | 需上传原视频到服务器 | 只上传 30 MB 音频 |
| **服务器负载** | FFmpeg 占 CPU | 零负载 |
| **速度** | 最快（原生 FFmpeg） | 慢 3-5 倍（WASM） |
| **文件大小限制** | 无限制 | 受浏览器内存限制 |
| **适用场景** | 有 GPU 服务器 | 轻量部署 / 无服务器 |

> 💡 **fflate vs JSZip**：`fflate` 只有 ~7 KB gzipped，比 JSZip（~40 KB）小 5 倍，且纯同步 API 更简单。对于"把几个 MP4 文件打成 ZIP"这种简单场景，fflate 是最佳选择。
### 5.4 导出格式：ZIP 打包与剪映草稿协议

切片完成后，用户需要以不同格式拿到结果。最常见的是三种导出方式：

```
三种导出格式：

  1. ZIP 打包下载（通用）
  ═══════════════════════════════════════
  • 内容：N 个 MP4 + 1 个 SRT 字幕文件
  • 文件名：01_标题.mp4, 02_标题.mp4, ...
  • 适合：直接发布抖音/快手/B站

  2. SRT 字幕文件
  ═══════════════════════════════════════
  • 标准字幕格式，用户导入剪映/PR 手动裁切
  • 适合：需要精细调整的场景

  3. 剪映草稿导出（进阶）
  ═══════════════════════════════════════
  • 生成剪映 draft_content.json 草稿文件
  • 用户在剪映中一键导入，切片已经放好时间线
  • 适合：深度剪映用户
```

**SRT 字幕导出：**

```python
def generate_srt(clips: list[dict]) -> str:
    """生成 SRT 字幕文件"""
    lines = []
    for i, clip in enumerate(clips, 1):
        start = _format_srt_time(clip["start_time"])
        end = _format_srt_time(clip["end_time"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(clip.get("title", f"片段 {i}"))
        lines.append("")  # 空行分隔
    return "\n".join(lines)

def _format_srt_time(seconds: float) -> str:
    """秒数转 SRT 时间格式 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{int(s):02d},{ms:03d}"
```

**剪映草稿导出的核心思路：**

```
剪映草稿结构（简化）：

  draft_content.json
  ├── tracks[]                    ← 时间线轨道
  │   └── segments[]              ← 每个片段
  │       ├── material_id         ← 引用素材 ID
  │       ├── target_timerange    ← 在时间线上的位置
  │       │   ├── start           ← 起点（微秒）
  │       │   └── duration        ← 时长（微秒）
  │       └── source_timerange    ← 原素材中的裁切范围
  │           ├── start           ← 裁切起点（微秒）
  │           └── duration        ← 裁切时长（微秒）
  └── materials                   ← 素材库
      └── videos[]
          ├── id                  ← 素材 ID
          └── path                ← 本地视频路径

  关键单位：剪映用微秒（1 秒 = 1,000,000 微秒）
```

> 💡 **剪映草稿的局限**：草稿中的视频路径是用户本地绝对路径（如 `/Users/xxx/video.mp4`），换台电脑就失效。这是剪映的设计限制，不是我们能解决的。导出时需要提示用户"请确保原视频在本地可访问"。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **重编码切片** | `-c:v libx264 -crf 23`，精确到毫秒，质量几乎无损 |
| **流拷贝切片** | `-c copy`，极快但起止点对齐到关键帧，精度差 |
| **批量容错** | 单段失败继续，返回"9/10 成功"而非全部报错 |
| **浏览器端切片** | FFmpeg.wasm + WORKERFS，原视频不离开用户电脑 |
| **ZIP 打包** | fflate（7 KB），同步 API，轻量高效 |
| **剪映草稿** | 时间单位是微秒，路径是本地绝对路径 |

---

## 6. 第五层：管线调度与状态管理

前四层解决了"怎么处理视频"的问题，这一层解决"怎么可靠地运行这个处理过程"。视频处理动辄几分钟甚至十几分钟，不可能让用户在 HTTP 请求里等——需要异步任务队列、进度追踪、实时推送、错误恢复的完整调度能力。

### 6.1 异步任务调度：ARQ Worker 实战

视频处理是典型的"提交后台任务 → 轮询/推送进度 → 获取结果"场景。我们用 ARQ（基于 Redis 的 Python 异步任务队列）来实现：

```python
"""ARQ Worker 任务入口"""
import redis.asyncio as aioredis
from app.config import settings
from app.services.transcriber import get_transcriber
from app.services.analyzer import ClipAnalyzer
from app.services.clipper import batch_clip, extract_audio

async def process_video(ctx: dict, task_id: str):
    """完整的视频处理 pipeline"""
    redis = aioredis.from_url(settings.redis_url)
    
    try:
        # Step 1: 读取视频 / 确认音频 (0% → 10%)
        # Step 2: 提取音频 (10% → 15%)
        # Step 3: 语音转录 (15% → 60%)
        # Step 4: LLM 分析 (60% → 80%)
        # Step 5: FFmpeg 切片 (80% → 90%)
        # Step 6: 存储 + 写数据库 (90% → 100%)
        pass  # 详见下方完整流程
    except Exception as e:
        # 错误处理（见 6.4）
        raise
    finally:
        await redis.aclose()
```

```
为什么选 ARQ 而不是 Celery？

  ARQ
  ═══════════════════════════════════════
  • 纯 asyncio（和 FastAPI 天然契合）
  • 依赖只有 Redis（极轻量）
  • 配置简单（一个 Python 文件）
  • 适合：中小规模、Python async 生态
  
  Celery
  ═══════════════════════════════════════
  • 同步模型为主（async 支持有限）
  • 功能强大（定时任务、链式任务、Canvas）
  • 生态庞大但配置复杂
  • 适合：大规模、Java/Python 混合团队
  
  对于视频处理管线来说：
  ─────────────────────────────────
  任务粒度大（一个任务跑 5-10 分钟）
  并发量低（同时处理 5-10 个视频）
  → ARQ 绰绰有余，且和 FastAPI 的 async 完美搭配
```

### 6.2 Pipeline 状态机与进度追踪

视频处理是一个多阶段的长流程，需要精确的状态管理：

```
Pipeline 状态机：

  ┌──────────┐
  │ pending  │ ← 任务刚创建
  └────┬─────┘
       │ ARQ Worker 拿到任务
       ▼
  ┌──────────────┐
  │ downloading  │ ← 读取/确认视频文件
  └────┬─────────┘
       ▼
  ┌──────────────┐
  │ transcribing │ ← 语音转录中（最慢，60%+ 时间）
  └────┬─────────┘
       ▼
  ┌──────────────┐
  │  analyzing   │ ← LLM 分析精彩片段
  └────┬─────────┘
       ▼
  ┌──────────────┐
  │  clipping    │ ← FFmpeg 批量切片
  └────┬─────────┘
       ▼
  ┌──────────────┐
  │  uploading   │ ← 保存到存储 + 写数据库
  └────┬─────────┘
       ▼
  ┌──────────┐
  │   done   │ ← 全部完成
  └──────────┘
  
  任何阶段出错 → failed（带 error_message）
```

**进度更新实现：**

```python
async def update_task_progress(
    redis, db, task,
    progress: int,
    message: str,
    status: str | None = None,
    persist: bool = True,
):
    """更新任务进度（数据库 + Redis 双写）"""
    # 1. 更新数据库（持久化）
    task.progress = progress
    task.progress_message = message
    if status:
        task.status = status
    if persist:
        await db.commit()
    
    # 2. 发布到 Redis（实时推送用）
    await redis.publish(
        f"task:{task.id}:progress",
        json.dumps({
            "progress": progress,
            "message": message,
            "status": status or task.status,
        }),
    )
```

| 进度区间 | 阶段 | 说明 |
|:---|:---|:---|
| 0% → 10% | downloading | 确认文件存在、读取时长 |
| 10% → 15% | transcribing | 提取音频（或跳过，音频直传模式） |
| 15% → 60% | transcribing | 语音转录（最慢的阶段） |
| 60% → 80% | analyzing | LLM 分析 |
| 80% → 90% | clipping | FFmpeg 批量切片 |
| 90% → 100% | uploading | 存储 + 写数据库 |

> 💡 **进度百分比不要均匀分配**：转录占 60%+ 的实际耗时，所以给它最大的进度区间（15%→60%）。如果均匀分成 6 段每段 16%，用户会看到"卡在 33% 不动了"——因为转录在跑，但进度条已经没空间了。

### 6.3 SSE 实时推送：让前端"看见"后端进度

前端需要实时知道后端处理到哪一步了。SSE（Server-Sent Events）是最简单的方案——单向推送，浏览器原生支持，不需要 WebSocket 的复杂性。

```python
"""SSE 进度推送端点"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI()

@app.get("/api/tasks/{task_id}/progress")
async def stream_progress(task_id: str):
    """SSE 端点：实时推送任务进度"""
    
    async def event_generator():
        redis = aioredis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"task:{task_id}:progress")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"
                    
                    # 终态检测：done 或 failed 后关闭连接
                    parsed = json.loads(data)
                    if parsed.get("status") in ("done", "failed"):
                        break
        finally:
            await pubsub.unsubscribe()
            await redis.aclose()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 禁用缓冲
        },
    )
```

```
前端监听 SSE：

  const source = new EventSource(`/api/tasks/${taskId}/progress`);
  
  source.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateProgressBar(data.progress);    // 0-100
    updateStatusText(data.message);      // "正在转录..."
    
    if (data.status === "done" || data.status === "failed") {
      source.close();
    }
  };
```

> 💡 **Nginx 的 `X-Accel-Buffering: no`**：Nginx 默认会缓冲 upstream 响应，导致 SSE 消息积攒后一次性发送。加上这个头可以禁用缓冲，实现真正的逐条推送。

### 6.4 错误恢复与资源清理

视频处理管线中任何一步都可能失败，必须做到：失败时正确记录状态、清理临时文件、不泄露资源。

```python
async def process_video(ctx: dict, task_id: str):
    """带完整错误恢复的 pipeline"""
    work_dir = os.path.join(settings.temp_dir, task_id)
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # ... 正常处理流程 ...
        pass
        
    except Exception as e:
        logger.exception(f"Task {task_id} failed: {e}")
        error_msg = f"处理失败: {str(e)[:180]}"
        
        try:
            await db.rollback()  # 回滚脏状态
            task.error_message = str(e)[:500]
            await update_task_progress(
                redis, db, task, task.progress,
                error_msg, "failed",
            )
        except Exception:
            # 连错误状态都写不进去 → 强制 commit
            await db.rollback()
            task.status = "failed"
            task.error_message = str(e)[:500]
            await db.commit()
        raise
        
    finally:
        # 无论成功失败，都清理临时文件
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
        await redis.aclose()
```

```
错误恢复的三层防御：

  第 1 层：正常错误处理
  ═══════════════════════════════════════
  try/except 捕获异常
  → rollback 清理事务
  → 更新状态为 failed + error_message
  → 用户看到 "处理失败: xxx"
  
  第 2 层：错误状态写入也失败
  ═══════════════════════════════════════
  再次 rollback
  → 直接设 status = "failed"
  → 强制 commit
  → 至少保证任务不会永远卡在 "processing"
  
  第 3 层：finally 清理
  ═══════════════════════════════════════
  无论如何都执行：
  → 删除临时文件（shutil.rmtree + ignore_errors）
  → 关闭 Redis 连接
  → 防止磁盘空间和连接泄露
```

> 💡 **`ignore_errors=True` 的必要性**：临时文件可能因为进程中断而处于锁定状态，`shutil.rmtree` 默认会抛异常。加上 `ignore_errors=True` 确保清理过程本身不会再抛错，避免掩盖真正的错误信息。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **ARQ** | 基于 Redis 的 async 任务队列，和 FastAPI 天然契合 |
| **状态机** | pending → downloading → transcribing → analyzing → clipping → done |
| **进度分配** | 按实际耗时比例分配百分比，转录占最大区间 |
| **SSE** | 单向推送，浏览器原生支持，比 WebSocket 简单 |
| **三层容错** | 正常 rollback → 强制 commit → finally 清理 |
| **临时文件** | 用 work_dir 统一管理，finally 中 rmtree 清理 |

---

## 7. 生产级优化：性能、成本与可靠性

管线能跑起来只是第一步。要在生产环境中稳定运行，需要关注性能瓶颈、成本控制和可观测性。

### 7.1 性能基准：各方案的速度与资源开销

```
3 小时直播视频的端到端处理基准：

  阶段              GPU 服务器          Mac M2 Max         无 GPU 云服务器
  ─────────────────────────────────────────────────────────────────────
  音频提取          30s                30s                30s
  语音转录          3-8 min            10-15 min          1-2 min (云端)
  LLM 分析          10-30s             10-30s             10-30s
  视频切片          1-2 min            1-2 min            1-2 min
  ─────────────────────────────────────────────────────────────────────
  总计              ~5-12 min          ~12-18 min         ~3-5 min
  
  瓶颈分布：
  ═══════════════════════════════════════
  转录占 60-80% 的总耗时
  → 优化转录 = 优化整条管线
```

### 7.2 音频直传模式：体积缩减 99% 的架构优化

这是整条管线中**投入产出比最高**的优化——把音频提取从服务器端移到浏览器端：

```
传统模式 vs 音频直传模式：

  传统模式
  ═══════════════════════════════════════
  用户上传 2.5 GB 视频 → 服务器提取音频 → 转录 → 分析
  
  问题：上传 2.5 GB 需要 20-30 分钟（100Mbps 带宽）
  服务器需要 2.5 GB 磁盘存视频 + CPU 提取音频
  
  音频直传模式 ⭐
  ═══════════════════════════════════════
  浏览器本地提取 30 MB 音频 → 上传 30 MB → 转录 → 分析
  
  优势：
  • 上传时间：30 分钟 → 30 秒（缩减 98%）
  • 服务器存储：2.5 GB → 30 MB（缩减 99%）
  • 服务器 CPU：不需要提取音频
  • 用户体验：拖入视频 → 几秒后开始分析（而非等半小时上传）
```

| 指标 | 传统模式 | 音频直传模式 | 提升 |
|:---|:---|:---|:---|
| 上传时间 | 20-30 分钟 | 30 秒 | **60x** |
| 服务器存储 | 2.5 GB/任务 | 30 MB/任务 | **83x** |
| 带宽成本 | 高 | 极低 | **83x** |
| 用户等待感 | 漫长 | 几乎即时 | — |

### 7.3 成本控制：本地推理 vs 云端 API 的经济学

```
每条 3 小时直播的处理成本：

  方案 A：全本地（GPU 服务器）
  ═══════════════════════════════════════
  转录：免费（本地 Whisper）
  分析：¥0.03（DeepSeek V3，27K Token）
  服务器：¥0.5/小时（按量付费 GPU 实例）
  ──────────────────────────────────
  单次总成本：约 ¥0.1-0.5
  
  方案 B：全云端（无 GPU）
  ═══════════════════════════════════════
  转录：¥2.4（阿里云 ASR，3 小时 × ¥0.8/小时）
  分析：¥0.03（DeepSeek V3）
  服务器：¥0.1/小时（轻量云服务器）
  ──────────────────────────────────
  单次总成本：约 ¥2.5-3.0
  
  方案 C：Mac 本地开发
  ═══════════════════════════════════════
  转录：免费（mlx-whisper）
  分析：¥0.03（DeepSeek V3）
  服务器：免费（本机）
  ──────────────────────────────────
  单次总成本：约 ¥0.03
```

> 💡 **成本最优路径**：日处理量 < 10 条用 Mac 本地（近乎免费）；10-50 条用阿里云 ASR（¥2.5/条但无需 GPU）；50+ 条租 GPU 服务器跑本地 Whisper（¥0.5/条但需要月租 GPU）。

### 7.4 监控与可观测性

生产环境必须能回答这些问题：哪些任务失败了？转录耗时是否异常？LLM 分析成功率如何？

```
关键监控指标：

  📊 任务级别
  ═══════════════════════════════════════
  • 任务成功率（done / total）
  • 各阶段平均耗时
  • 失败原因分布

  📊 ASR 级别
  ═══════════════════════════════════════
  • 转录段数 / 音频时长比
  • 空转录率（0 段结果的比例）
  • 各 Transcriber 类型的使用比例

  📊 LLM 级别
  ═══════════════════════════════════════
  • 批次成功率
  • JSON 解析成功率（直接解析 vs 正则兜底 vs 失败）
  • 平均每批识别的 clip 数量
  
  📊 系统级别
  ═══════════════════════════════════════
  • Redis 连接数
  • 临时文件目录大小
  • ARQ 队列积压量
```

> 💡 **最小可行监控**：至少在 Worker 日志中记录每个阶段的耗时和结果数量。用 `logger.info(f"Task {task_id}: 转录完成，共 {len(transcript)} 段")` 这种结构化日志，后续可以用 Loki/ELK 做分析。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **性能瓶颈** | 转录占 60-80% 总耗时，优化转录 = 优化管线 |
| **音频直传** | 浏览器提取音频，上传 30 MB 而非 2.5 GB，用户体验质变 |
| **成本阶梯** | <10 条/天用 Mac，10-50 用云端 ASR，50+ 租 GPU |
| **监控重点** | 任务成功率、转录段数、JSON 解析成功率、队列积压 |

---

## 8. 实战案例：构建一个直播切片 Agent

理论讲完了，现在把前 7 章的所有技术串联起来，构建一个完整的直播切片系统。

### 8.1 项目架构与核心模块

```
项目目录结构：

  ai-slice/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py                  ← FastAPI 入口
  │   │   ├── config.py                ← 环境变量配置
  │   │   ├── models/                  ← SQLAlchemy 模型
  │   │   ├── routes/                  ← API 路由
  │   │   │   ├── tasks.py             ← 任务 CRUD + SSE 推送
  │   │   │   └── clips.py             ← 切片查询 + 下载
  │   │   ├── services/                ← 核心业务逻辑
  │   │   │   ├── transcriber.py       ← ASR 统一接口 + 工厂
  │   │   │   ├── analyzer.py          ← LLM 分析 + JSON 解析
  │   │   │   └── clipper.py           ← FFmpeg 切片 + 音频提取
  │   │   └── workers/
  │   │       └── pipeline.py          ← ARQ 任务（主管线）
  │   ├── requirements.txt
  │   └── Dockerfile
  ├── frontend/
  │   ├── src/
  │   │   ├── services/
  │   │   │   ├── audioExtractor.ts     ← FFmpeg.wasm 音频提取
  │   │   │   ├── ffmpegRuntime.ts      ← FFmpeg 实例管理
  │   │   │   └── localClipper.ts       ← 浏览器端切片
  │   │   └── components/
  │   │       ├── VideoUploader.tsx      ← 拖拽上传 + 音频提取
  │   │       └── ProgressViewer.tsx     ← SSE 进度展示
  │   └── package.json
  └── docker-compose.yml               ← Redis + PostgreSQL + Worker
```

### 8.2 端到端流程：从用户上传到切片下载

```
完整处理流程（时间线视角）：

  T+0s    用户拖入 3h 直播视频
          ├── 浏览器：FFmpeg.wasm 开始提取音频
          └── 显示："正在提取音频..."
  
  T+30s   音频提取完成（30 MB MP3）
          ├── 浏览器：上传音频 + 视频元数据到后端
          └── 显示："正在上传..."
  
  T+35s   后端创建 Task，入 ARQ 队列
          ├── 返回 task_id
          └── 前端连接 SSE 监听进度
  
  T+40s   ARQ Worker 开始处理
          ├── 确认音频文件（10%）
          └── 开始转录（15%）
  
  T+5min  转录完成（60%）
          ├── 获得 500+ 段带时间戳文本
          └── 开始 LLM 分析
  
  T+6min  LLM 分析完成（80%）
          ├── 识别出 12 个精彩片段
          ├── 去重后保留 10 个
          └── 开始切片 / 或返回切片方案给前端
  
  T+8min  切片完成（100%）
          ├── 10 个 MP4 文件打包
          └── SSE 推送 done
  
  T+8min  用户下载 ZIP
          ├── 10 个切片视频 + SRT 字幕
          └── 总耗时 < 10 分钟（全自动）
```

### 8.3 前后端协作：浏览器提取 + 后端分析的混合架构

```
混合架构的数据流：

  ┌──────────────── 浏览器 ────────────────┐
  │                                         │
  │  原视频 (2.5GB)                          │
  │      │                                  │
  │      ▼ FFmpeg.wasm                       │
  │  音频 (30MB) ───────────────────────────┼──▶ 后端 API
  │      │                                  │    ├── ASR 转录
  │  [保持 File handle]                      │    ├── LLM 分析
  │      │                                  │    └── 返回切片方案
  │      │           ◀──── SSE 进度推送 ─────┼──── 后端
  │      │           ◀──── 切片方案 JSON ────┼──── 后端
  │      │                                  │
  │      ▼ FFmpeg.wasm                       │
  │  本地切片（可选）                          │
  │      │                                  │
  │      ▼ fflate                            │
  │  ZIP 下载                                │
  │                                         │
  └─────────────────────────────────────────┘
  
  核心优势：
  ═══════════════════════════════════════
  1. 2.5 GB 视频永远不离开用户电脑
  2. 服务器只处理 30 MB 音频 + 5 KB JSON
  3. 服务器零 FFmpeg 负载（切片在浏览器完成）
  4. 可以部署在最便宜的无 GPU 云服务器上
```

> 💡 **这个架构的本质**：把计算密集的 I/O 操作（音频提取、视频切片）卸载到客户端，服务器只做"智力活"（转录 + 分析）。用户的电脑就是算力节点。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **项目结构** | services/ 封装业务逻辑，workers/ 封装异步任务，routes/ 暴露 API |
| **端到端耗时** | 3 小时视频 < 10 分钟全自动处理 |
| **混合架构** | 浏览器做 I/O 密集操作，服务器做 AI 分析 |
| **设计本质** | 用户电脑就是算力节点，服务器只做"智力活" |

---

## 9. 前沿展望：多模态原生理解与端到端管线

我们构建的整条管线本质上是一个"拆解再理解"的方案——把视频拆成音频、文本、再用 AI 理解文本。但这个方案正在被新一代多模态模型挑战。

### 9.1 原生视频理解：跳过"拆解"直接"看懂"

```
当前管线 vs 未来可能：

  当前（2024-2025）
  ═══════════════════════════════════════
  视频 → 音频 → 文本 → LLM 分析
  
  四次模态转换，每次都有信息损失：
  • 视频 → 音频：丢失画面信息
  • 音频 → 文本：ASR 有 4-5% 错误率
  • 文本 → LLM：上下文窗口限制
  
  未来（2026+）
  ═══════════════════════════════════════
  视频 → 多模态 LLM → 切片方案
  
  一次输入，直接输出：
  • 模型直接"看"视频 + "听"音频
  • 理解画面变化（表情、动作、弹幕）
  • 结合语音语义做综合判断
```

Gemini 2.5 已经支持最长 1 小时的视频输入，但目前的限制：

| 能力 | 当前状态 | 制约因素 |
|:---|:---|:---|
| 视频输入 | ≤1 小时 | 上下文窗口 + 计算成本 |
| 时间精度 | ~5 秒级 | 视频采样率（1-2 fps） |
| 成本 | 高 | 视频 Token 消耗巨大 |
| 中文支持 | 一般 | 训练数据偏英文 |

### 9.2 从管线到 Agent：自主决策的视频处理系统

```
管线模式 vs Agent 模式：

  管线（Pipeline）
  ═══════════════════════════════════════
  固定流程：A → B → C → D
  每步固定执行，不会因内容临时调整
  
  优点：可预测、可调试、成本可控
  缺点：不灵活，对所有视频用同一个流程
  
  Agent
  ═══════════════════════════════════════
  自主决策：观察 → 思考 → 行动 → 观察 → ...
  
  示例决策链：
  1. 探测视频："这是一个游戏直播，3 小时"
  2. 决策："游戏直播应该关注操作高光和搞笑时刻"
  3. 调整 Prompt："重点关注击杀、翻盘、搞笑失误"
  4. 转录后发现有大量英文："切换 ASR 语言为英文"
  5. 分析结果太多："提高 virality_score 阈值到 7"
  
  优点：适应性强，不同视频类型不同策略
  缺点：不可预测、调试困难、成本可能加倍
```

### 9.3 技术演进路线图

```
AI 视频处理的技术演进：

  2023 ─── Whisper 成熟 + GPT-4 发布
  │        ✅ "音频转文本 + LLM 分析" 范式确立
  │
  2024 ─── Gemini 支持视频输入 + DeepSeek 降低成本
  │        ✅ 管线方案成本降到 ¥0.03-3/条
  │        ⬜ 多模态视频理解能力有限
  │
  2025 ─── 多模态模型视频理解能力增强
  │        ✅ 短视频（<30min）可直接多模态分析
  │        ⬜ 长视频仍需管线方案
  │
  2026 ─── 预期：长视频原生理解成为可能
  │        ⬜ 3 小时视频直接输入
  │        ⬜ 成本降到可接受范围
  │
  未来 ─── 端到端视频 Agent
           ⬜ 自主决策处理策略
           ⬜ 同时理解画面 + 语音 + 弹幕 + 评论
           ⬜ 自动生成带字幕、特效的成片
```

> 💡 **务实的建议**：管线方案在 2-3 年内仍然是最可靠、最经济的选择。多模态原生理解目前更适合作为管线的"增强"（比如用 Gemini 验证 LLM 选出的片段是否真的有画面冲击力），而非"替代"。当你能用 ¥0.03 处理一条 3 小时视频时，没有理由花 ¥10 去让多模态模型"直接看"。

---

> 🎉 **全文完**。从视频的第一个字节到最后一个切片文件，我们完整拆解了 AI 视频处理管线的每一层。核心思路始终不变：**把视频"翻译"成 AI 擅长的文本，让 AI 做它擅长的事——理解语义**。管线设计、工厂模式、容错解析、浏览器端计算……这些工程能力才是把 AI 能力落地成产品的关键。
