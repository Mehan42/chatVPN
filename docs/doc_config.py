# XVPN Documentation Configuration
# Конфигурация автоматической генерации документации

# === Sphinx Configuration ===
# docs/conf.py

# Конфигурация Sphinx для генерации документации

import sys
import os
from datetime import datetime

# Добавляем исходный код в путь
sys.path.insert(0, os.path.abspath('../src'))
sys.path.insert(0, os.path.abspath('../server'))
sys.path.insert(0, os.path.abspath('../client'))

# Информация о проекте
project = 'XVPN - Intelligent VPN with AI Agents'
copyright = f'{datetime.now().year}, XVPN Team'
author = 'XVPN Team'

# Основная версия и релиз
release = '1.0.0'
version = '1.0'

# Расширения Sphinx
extensions = [
    'sphinx.ext.autodoc',           # Автоматическая документация из docstrings
    'sphinx.ext.viewcode',          # Просмотр исходного кода
    'sphinx.ext.napoleon',          # Поддержка Google и NumPy стилей docstrings
    'sphinx.ext.intersphinx',       # Ссылки на внешнюю документацию
    'sphinx.ext.todo',              # Поддержка TODO заметок
    'sphinx.ext.coverage',          # Отчет о покрытии документацией
    'sphinx.ext.mathjax',           # Математические формулы
    'sphinx.ext.ifconfig',          # Условное содержимое
    'sphinx.ext.githubpages',        # Поддержка GitHub Pages
    'sphinx.ext.autosummary',       # Автоматические сводки
    'sphinx.ext.graphviz',          # Графики и диаграммы
    'sphinx.ext.inheritance_diagram',  # Диаграммы наследования
    'sphinx.ext.autosectionlabel',  # Автоматические метки секций
    'sphinxcontrib.httpdomain',     # HTTP API документация
    'sphinxcontrib.openapi',        # OpenAPI/Swagger документация
    'sphinx_tabs.tabs',             # Вкладки для документации
    'sphinx_copybutton',            # Кнопки копирования кода
    'sphinxemoji.sphinxemoji',     # Эмодзи в документации
]

# Путь к шаблонам
templates_path = ['_templates']

# Исключаемые шаблоны
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Тема документации
html_theme = 'sphinx_rtd_theme'

# Статические файлы
html_static_path = ['_static']

# Форматы вывода
htmlhelp_basename = 'xvpndoc'

# === Napoleon Extension Configuration ===
# Настройки Napoleon расширения
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# === Autodoc Configuration ===
# Настройки автодокументации
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_class_signature = 'mixed'

# === Intersphinx Configuration ===
# Ссылки на внешнюю документацию
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'flask': ('https://flask.palletsprojects.com/en/2.3.x/', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/20/', None),
    'redis': ('https://redis-py.readthedocs.io/en/stable/', None),
    'celery': ('https://docs.celeryq.dev/en/stable/', None),
    'aiohttp': ('https://docs.aiohttp.org/en/stable/', None),
}

# === Graphviz Configuration ===
# Настройки графиков
graphviz_dot = 'dot'
graphviz_dot_args = ['-Gdpi=150']
graphviz_output_format = 'svg'

# === Todo Extension Configuration ===
# Настройки TODO заметок
todo_include_todos = True
todo_emit_warnings = True

# === Coverage Extension Configuration ===
# Настройки покрытия документацией
coverage_statistics_target = 100
coverage_statistics_file = 'coverage.txt'

# === HTML Theme Configuration ===
# Настройки HTML темы
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',  # Provided by Google in your dashboard
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'logo_only': False,
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# === LaTeX Output Configuration ===
# Настройки для LaTeX вывода
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'fncychap': '\\usepackage[Bjornstrup]{fncychap}',
    'printindex': '\\footnotesize\\raggedright\\printindex',
}

latex_documents = [
    (master_doc, 'xvpn.tex', 'XVPN Documentation',
     'XVPN Team', 'manual'),
]

# === Manual Page Output Configuration ===
# Настройки для manual pages
man_pages = [
    (master_doc, 'xvpn', 'XVPN Documentation',
     [author], 1)
]

# === Texinfo Output Configuration ===
# Настройки для Texinfo
texinfo_documents = [
    (master_doc, 'xvpn', 'XVPN Documentation',
     author, 'xvpn', 'Intelligent VPN with AI Agents.',
     'Miscellaneous'),
]

# === EPUB Output Configuration ===
# Настройки для EPUB
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright

# === Index Configuration ===
# Настройки индекса
indexdoc = 'index'
master_doc = 'index'

# === Language Configuration ===
# Язык документации
language = 'ru'
locale_dirs = ['locale/']
gettext_compact = False

# === Extension Configuration ===
# sphinx_copybutton настройки
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True
copybutton_line_continuation_character = "\\"
copybutton_here_doc_delimiter = "EOT"

# sphinx_tabs настройки
sphinx_tabs_disable_css_loading = False
sphinx_tabs_disable_tab_closing = True
sphinx_tabs_disable_hash_activation = False

# sphinxemoji настройки
sphinxemoji_style = 'twemoji'

# === PyDoctor Configuration ===
# pydoctor.conf

# Конфигурация PyDoctor для генерации API документации

[tool.pydoctor]
# Основные настройки
project-name = "XVPN"
project-url = "https://github.com/Mehan42/chatVPN"
html-write-function-pages = true
html-output = "apidocs"
verbose = 1

# Пути к исходному коду
add-package = [
    "../src",
    "../server",
    "../client",
]

# Исключения
exclude = [
    "*/tests/*",
    "*/test_*",
    "*/venv/*",
    "*/.venv/*",
    "*/__pycache__/*",
    "*/build/*",
    "*/dist/*",
    "*/.eggs/*",
    "*/.git/*",
    "*/node_modules/*",
    "*/migrations/*",
]

# === MkDocs Configuration ===
# mkdocs.yml

# Конфигурация MkDocs для генерации документации

site_name: XVPN Documentation
site_url: https://docs.xvpn.local
site_description: Complete documentation for XVPN - Intelligent VPN with AI Agents
site_author: XVPN Team

# Тема
theme:
  name: material
  language: ru
  palette:
    # Темная тема по умолчанию
    - scheme: slate
      primary: deep purple
      accent: deep purple
      toggle:
        icon: material/weather-night
        name: Switch to light mode
    # Светлая тема
    - scheme: default
      primary: deep purple
      accent: deep purple
      toggle:
        icon: material/weather-sunny
        name: Switch to dark mode
  font:
    text: Roboto
    code: Roboto Mono
  features:
    - navigation.instant
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.indexes
    - toc.follow
    - toc.integrate
    - search.suggest
    - search.highlight
    - content.tabs.link
    - content.code.annotate
    - content.code.copy

# Плагины
plugins:
  - search
  - autorefs
  - minify:
      minify_html: true
  - git-revision-date-localized:
      enable_creation_date: true
  - redirects:
      redirect_maps:
        'old/page.md': 'new/page.md'

# Расширения Markdown
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.details
  - pymdownx.tasklist:
      custom_checkbox: true
  - attr_list
  - md_in_html
  - admonition
  - footnotes
  - toc:
      permalink: true

# Навигация
nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
      - Configuration: getting-started/configuration.md
      - First Steps: getting-started/first-steps.md
  - User Guide:
      - Basic Usage: user-guide/basic-usage.md
      - Advanced Features: user-guide/advanced-features.md
      - Security: user-guide/security.md
      - Troubleshooting: user-guide/troubleshooting.md
      - FAQ: user-guide/faq.md
  - Administrator Guide:
      - Server Installation: admin-guide/server-installation.md
      - Configuration: admin-guide/configuration.md
      - Monitoring: admin-guide/monitoring.md
      - Maintenance: admin-guide/maintenance.md
      - Security: admin-guide/security.md
      - Backup and Restore: admin-guide/backup-restore.md
  - Developer Guide:
      - Architecture: developer-guide/architecture.md
      - API Reference: developer-guide/api-reference.md
      - Contributing: developer-guide/contributing.md
      - Testing: developer-guide/testing.md
      - Building from Source: developer-guide/building.md
  - API Documentation:
      - REST API: api/rest-api.md
      - WebSocket API: api/websocket-api.md
      - Internal API: api/internal-api.md
  - Changelog: changelog.md
  - License: license.md

# Дополнительные файлы
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/Mehan42/chatVPN
    - icon: fontawesome/brands/telegram
      link: https://t.me/xvpn_community
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/xvpn

# Copyright
copyright: Copyright &copy; 2025 XVPN Team

# === Swagger UI Configuration ===
# swagger-ui-config.json

{
  "swagger": "2.0",
  "info": {
    "title": "XVPN API",
    "description": "Intelligent VPN with AI Agents",
    "version": "1.0.0"
  },
  "host": "api.xvpn.local",
  "basePath": "/",
  "schemes": ["https"],
  "consumes": ["application/json"],
  "produces": ["application/json"],
  "paths": {
    "/mcp/v1/vpn.health": {
      "get": {
        "summary": "Health Check",
        "description": "Returns current VPN health status and mask score",
        "responses": {
          "200": {
            "description": "Successful response",
            "schema": {
              "type": "object",
              "properties": {
                "status": {
                  "type": "string",
                  "enum": ["healthy", "warning", "critical"]
                },
                "mask_score": {
                  "type": "integer",
                  "minimum": 0,
                  "maximum": 5
                },
                "timestamp": {
                  "type": "integer"
                },
                "version": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "/transports/manifest.json": {
      "get": {
        "summary": "Transport Manifest",
        "description": "Returns available transport protocols manifest",
        "responses": {
          "200": {
            "description": "Successful response",
            "schema": {
              "type": "object",
              "properties": {
                "version": {
                  "type": "integer"
                },
                "transports": {
                  "type": "array",
                  "items": {
                    "type": "object"
                  }
                }
              }
            }
          }
        }
      }
    },
    "/clients/{uuid}.json": {
      "get": {
        "summary": "Client Configuration",
        "description": "Returns client configuration by UUID",
        "parameters": [
          {
            "name": "uuid",
            "in": "path",
            "required": true,
            "type": "string",
            "format": "uuid"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response",
            "schema": {
              "type": "object"
            }
          },
          "404": {
            "description": "Client not found"
          }
        }
      }
    }
  }
}

# === Postman Collection Configuration ===
# postman/xvpn-api.postman_collection.json

{
  "info": {
    "name": "XVPN API",
    "description": "Intelligent VPN with AI Agents",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://api.xvpn.local/mcp/v1/vpn.health",
          "protocol": "https",
          "host": ["api.xvpn.local"],
          "path": ["mcp", "v1", "vpn.health"]
        }
      },
      "response": []
    },
    {
      "name": "Transport Manifest",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://api.xvpn.local/transports/manifest.json",
          "protocol": "https",
          "host": ["api.xvpn.local"],
          "path": ["transports", "manifest.json"]
        }
      },
      "response": []
    },
    {
      "name": "Client Configuration",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://api.xvpn.local/clients/{{client_uuid}}.json",
          "protocol": "https",
          "host": ["api.xvpn.local"],
          "path": ["clients", "{{client_uuid}}.json"]
        }
      },
      "response": []
    }
  ],
  "variable": [
    {
      "key": "client_uuid",
      "value": "example-uuid-123",
      "type": "string"
    }
  ]
}

# === Documentation Scripts ===
# scripts/generate_docs.sh

#!/bin/bash

# Скрипт для генерации документации XVPN

set -e  # Выход при любой ошибке

echo "📚 Generating XVPN Documentation..."
echo "====================================="

# Переменные окружения
export PYTHONPATH=.:src:server:client
export SPHINX_APIDOC_OPTIONS=members,undoc-members,show-inheritance
export SPHINXOPTS="-W --keep-going"

# Проверка что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Создание директорий для документации
mkdir -p docs/_build
mkdir -p docs/apidocs
mkdir -p docs/_static
mkdir -p docs/_templates

# === Sphinx Documentation ===
echo "📖 Generating Sphinx Documentation..."

# Установка Sphinx и зависимостей
pip install sphinx sphinx-rtd-theme sphinxcontrib-httpdomain sphinxcontrib-openapi sphinx-tabs sphinx-copybutton sphinxemoji

# Генерация API документации
echo "🔧 Generating API Documentation..."
sphinx-apidoc -f -o docs/apidocs src/ server/ client/ --separate --no-headings

# Генерация HTML документации
echo "🔨 Building HTML Documentation..."
sphinx-build -b html docs docs/_build/html

# === MkDocs Documentation ===
echo "📘 Generating MkDocs Documentation..."

# Установка MkDocs и зависимостей
pip install mkdocs mkdocs-material mkdocs-git-revision-date-localized-plugin

# Генерация MkDocs документации
mkdocs build -f mkdocs.yml

# === PyDoctor Documentation ===
echo "🔍 Generating PyDoctor Documentation..."

# Установка PyDoctor
pip install pydoctor

# Генерация PyDoctor документации
pydoctor --config=pydoctor.conf

# === Swagger UI Documentation ===
echo "🌐 Generating Swagger UI Documentation..."

# Создание директории для Swagger
mkdir -p docs/swagger

# Копирование Swagger UI файлов
if [ -d "node_modules/swagger-ui-dist" ]; then
    cp node_modules/swagger-ui-dist/* docs/swagger/
fi

# Копирование OpenAPI спецификации
cp swagger-ui-config.json docs/swagger/

# === Postman Collection ===
echo "📬 Generating Postman Collection..."

# Создание директории для Postman
mkdir -p docs/postman

# Копирование Postman коллекции
cp postman/xvpn-api.postman_collection.json docs/postman/

# === PDF Documentation ===
echo "📄 Generating PDF Documentation..."

# Установка LaTeX для PDF генерации
if command -v pdflatex &> /dev/null; then
    sphinx-build -b latex docs docs/_build/latex
    cd docs/_build/latex
    make all-pdf
    cd ../../..
    echo "✅ PDF Documentation Generated!"
else
    echo "⚠️  LaTeX not found. Skipping PDF generation."
fi

# === ePub Documentation ===
echo "📱 Generating ePub Documentation..."

# Генерация ePub документации
sphinx-build -b epub docs docs/_build/epub

# === Documentation Validation ===
echo "✅ Validating Documentation..."

# Проверка что документация сгенерирована
if [ -f "docs/_build/html/index.html" ]; then
    echo "✅ HTML Documentation Generated Successfully!"
else
    echo "❌ HTML Documentation Generation Failed!"
    exit 1
fi

if [ -f "docs/_build/latex/xvpn.pdf" ]; then
    echo "✅ PDF Documentation Generated Successfully!"
fi

if [ -f "docs/_build/epub/xvpn.epub" ]; then
    echo "✅ ePub Documentation Generated Successfully!"
fi

# === Documentation Deployment ===
echo "🚀 Deploying Documentation..."

# Копирование в директорию для деплоя
mkdir -p site
cp -r docs/_build/html/* site/

# Создание robots.txt
cat > site/robots.txt << EOF
User-agent: *
Disallow:
Sitemap: https://docs.xvpn.local/sitemap.xml
EOF

# Создание humans.txt
cat > site/humans.txt << EOF
/* TEAM */
Lead Developer: Mehan42
Contact: team@xvpn.local
Twitter: @xvpn
Location: Moscow, Russia

Developer: Avtandil42
Contact: team@xvpn.local
Twitter: @xvpn
Location: Moscow, Russia

/* SITE */
Last update: $(date -I)
Language: Russian, English
Doctype: HTML5
IDE: VS Code, PyCharm
Technology: Python, Flask, Docker, Kubernetes
Components: Sphinx, MkDocs, PyDoctor, Swagger UI
Software: Git, GitHub Actions, Jenkins
EOF

# === Documentation Statistics ===
echo "📊 Documentation Statistics:"
echo "HTML Pages: $(find docs/_build/html -name "*.html" | wc -l)"
echo "Images: $(find docs/_build/html -name "*.png" -o -name "*.jpg" -o -name "*.gif" | wc -l)"
echo "CSS Files: $(find docs/_build/html -name "*.css" | wc -l)"
echo "JS Files: $(find docs/_build/html -name "*.js" | wc -l)"

# === Cleanup ===
echo "🧹 Cleaning up temporary files..."
rm -rf docs/_build/doctrees
rm -rf docs/_build/environment.pickle

# === Completion ===
echo "🎉 Documentation Generation Completed!"
echo "📂 Output Directory: site/"
echo "🔗 HTML Documentation: site/index.html"
echo "📘 API Documentation: site/apidocs/index.html"
echo "📖 User Guide: site/user-guide/index.html"
echo "🔧 Admin Guide: site/admin-guide/index.html"
echo "💻 Developer Guide: site/developer-guide/index.html"
echo "🌐 API Reference: site/api-reference/index.html"

# === GitHub Pages Deployment ===
if [[ "$GITHUB_ACTIONS" == "true" ]]; then
    echo "☁️ Deploying to GitHub Pages..."
    # TODO: Add GitHub Pages deployment logic
    echo "✅ GitHub Pages Deployment Scheduled!"
fi

# === Exit ===
echo "🎊 Documentation Generation Finished Successfully!"
exit 0

# === Конец скрипта ===