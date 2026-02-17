<div align="center">

# 🍌 PaperBanana

**AI-Powered Academic Diagram Generation**

Generate publication-quality methodology diagrams and statistical plots from text descriptions using multi-agent AI.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?logo=opensourceinitiative&logoColor=white)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2601.23265-b31b1b?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2601.23265)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples)

</div>

---

## 📖 About

PaperBanana is an open-source Python framework that automatically generates academic diagrams from text descriptions. It uses a multi-agent AI pipeline with Google Gemini to create publication-ready illustrations for research papers.

> **Note**: This is an unofficial, community-driven implementation inspired by the paper ["PaperBanana: Automating Academic Illustration for AI Scientists"](https://arxiv.org/abs/2601.23265) (arXiv:2601.23265). This project is not affiliated with the original authors or Google Research.

<p align="center">
  <img src="assets/img/hero_image.png" alt="PaperBanana workflow" width="800"/>
</p>

## ✨ Features

- **🤖 Multi-Agent Pipeline**: 5 specialized AI agents work together to plan, design, and refine diagrams
- **🎨 Two Diagram Types**:
  - Methodology diagrams (architecture, workflows, frameworks)
  - Statistical plots (charts, graphs, visualizations)
- **🔄 Iterative Refinement**: Automatic quality improvement through critic feedback (up to 3 rounds)
- **📚 Reference-Based Learning**: Uses 13 curated academic diagrams as examples
- **🎯 Style Guidelines**: Follows NeurIPS publication standards
- **🆓 Free to Use**: Powered by Google Gemini's free tier
- **🛠️ Multiple Interfaces**: CLI, Python API, and MCP server for IDE integration

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- A free Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Install from PyPI
pip install paperbanana

# Or install from source
git clone https://github.com/llmsresearch/paperbanana.git
cd paperbanana
pip install -e ".[dev,google]"
```

### Setup API Key

Run the interactive setup wizard:

```bash
paperbanana setup
```

Or configure manually:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# GOOGLE_API_KEY=your_api_key_here
```

### Generate Your First Diagram

```bash
# Generate a methodology diagram
paperbanana generate \
  --input examples/sample_inputs/transformer_method.txt \
  --caption "Overview of our encoder-decoder architecture"
```

Output will be saved to `outputs/run_<timestamp>/final_output.png`

## 📚 Documentation

### How It Works

PaperBanana uses a two-phase pipeline with 5 AI agents:

**Phase 1: Planning** (Linear)
1. **Retriever** - Finds relevant reference diagrams from curated examples
2. **Planner** - Creates detailed textual description of the target diagram
3. **Stylist** - Refines the description with NeurIPS-style guidelines

**Phase 2: Generation** (Iterative, up to 3 rounds)
4. **Visualizer** - Renders the description into an image
5. **Critic** - Evaluates quality and provides revision feedback

### CLI Commands

#### Generate Methodology Diagram

```bash
paperbanana generate \
  --input method.txt \
  --caption "Figure caption describing the diagram" \
  --output diagram.png \
  --iterations 3
```

**Options:**
- `--input, -i`: Path to methodology text file (required)
- `--caption, -c`: Figure caption/communicative intent (required)
- `--output, -o`: Output image path (default: auto-generated)
- `--iterations, -n`: Number of refinement rounds (default: 3)
- `--config`: Custom YAML config file

#### Generate Statistical Plot

```bash
paperbanana plot \
  --data results.csv \
  --intent "Bar chart comparing model accuracy across benchmarks"
```

**Options:**
- `--data, -d`: Path to CSV or JSON data file (required)
- `--intent`: Description of desired plot (required)
- `--output, -o`: Output image path
- `--iterations, -n`: Refinement rounds (default: 3)

#### Evaluate Diagram Quality

```bash
paperbanana evaluate \
  --generated my_diagram.png \
  --reference human_diagram.png \
  --context method.txt \
  --caption "Overview of framework"
```

Evaluates on 4 dimensions: Faithfulness, Readability, Conciseness, Aesthetics

### Python API

```python
import asyncio
from paperbanana import PaperBananaPipeline, GenerationInput, DiagramType
from paperbanana.core.config import Settings

# Configure the pipeline
settings = Settings(
    vlm_provider="gemini",
    image_provider="google_imagen",
    refinement_iterations=3,
)

pipeline = PaperBananaPipeline(settings=settings)

# Generate a diagram
result = asyncio.run(pipeline.generate(
    GenerationInput(
        source_context="Your methodology description here...",
        communicative_intent="Overview of the proposed method",
        diagram_type=DiagramType.METHODOLOGY,
    )
))

print(f"Generated diagram: {result.image_path}")
```

See `examples/` directory for more complete examples.

### MCP Server (IDE Integration)

Use PaperBanana directly in Claude Code, Cursor, or any MCP-compatible IDE:

```json
{
  "mcpServers": {
    "paperbanana": {
      "command": "uvx",
      "args": ["--from", "paperbanana[mcp]", "paperbanana-mcp"],
      "env": { "GOOGLE_API_KEY": "your-api-key" }
    }
  }
}
```

**Available tools:**
- `generate_diagram` - Create methodology diagrams
- `generate_plot` - Create statistical plots
- `evaluate_diagram` - Evaluate diagram quality

See [`mcp_server/README.md`](mcp_server/README.md) for detailed setup instructions.

## 💡 Examples

### Example 1: Transformer Architecture

**Input text** (`method.txt`):
```
Our model uses a standard encoder-decoder architecture. The encoder
processes input sequences through multi-head self-attention layers,
followed by position-wise feed-forward networks. The decoder generates
output tokens auto-regressively using masked self-attention and
cross-attention to encoder representations.
```

**Command:**
```bash
paperbanana generate -i method.txt -c "Transformer architecture overview"
```

### Example 2: Experimental Results

**Input data** (`results.csv`):
```csv
model,accuracy,f1_score
Baseline,0.75,0.72
Ours,0.89,0.87
SOTA,0.85,0.83
```

**Command:**
```bash
paperbanana plot -d results.csv --intent "Bar chart comparing model performance"
```

More examples in the `examples/` directory.

## ⚙️ Configuration

Default settings are in `configs/config.yaml`. Override with custom YAML:

```yaml
vlm:
  provider: gemini
  model: gemini-2.0-flash

image:
  provider: google_imagen
  model: gemini-3-pro-image-preview

pipeline:
  num_retrieval_examples: 10
  refinement_iterations: 3
  output_resolution: "2k"

output:
  dir: outputs
  save_iterations: true
  save_metadata: true
```

Use with:
```bash
paperbanana generate -i method.txt -c "Caption" --config my_config.yaml
```

## 🏗️ Project Structure

```
paperbanana/
├── paperbanana/          # Core package
│   ├── agents/           # 5 AI agents (Retriever, Planner, Stylist, Visualizer, Critic)
│   ├── core/             # Pipeline orchestration, config, types
│   ├── providers/        # VLM and image generation providers
│   ├── reference/        # Reference diagram management
│   └── evaluation/       # Quality evaluation system
├── configs/              # YAML configuration files
├── prompts/              # Agent prompt templates
├── data/
│   ├── reference_sets/   # 13 curated methodology diagrams
│   └── guidelines/       # NeurIPS style guidelines
├── examples/             # Example scripts and sample inputs
├── mcp_server/           # MCP server for IDE integration
└── tests/                # Test suite
```

## 🔧 Development

```bash
# Install with dev dependencies
pip install -e ".[dev,google]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=paperbanana --cov-report=xml

# Lint code
ruff check paperbanana/ mcp_server/ tests/ scripts/

# Format code
ruff format paperbanana/ mcp_server/ tests/ scripts/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📝 Citation

This is an **unofficial** implementation. If you use this work, please cite the **original paper**:

```bibtex
@article{zhu2026paperbanana,
  title={PaperBanana: Automating Academic Illustration for AI Scientists},
  author={Zhu, Dawei and Meng, Rui and Song, Yale and Wei, Xiyu
          and Li, Sujian and Pfister, Tomas and Yoon, Jinsung},
  journal={arXiv preprint arXiv:2601.23265},
  year={2026}
}
```

**Original paper**: [https://arxiv.org/abs/2601.23265](https://arxiv.org/abs/2601.23265)

## ⚠️ Disclaimer

This project is an independent open-source implementation based on the publicly available research paper. It is **not affiliated with, endorsed by, or connected to** the original authors, Google Research, or any associated institutions. The implementation may differ from the original system described in the paper.

## 🙏 Acknowledgments

- Original PaperBanana paper authors for the innovative research
- Google for providing free Gemini API access
- The open-source community for various dependencies

---

<div align="center">

Made with ❤️ by the open-source community

[Report Bug](https://github.com/llmsresearch/paperbanana/issues) • [Request Feature](https://github.com/llmsresearch/paperbanana/issues)

</div>
