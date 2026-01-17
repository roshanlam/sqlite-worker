# 🚀 Starter Templates

Ready-to-use project templates to jump-start your development with sqlite-worker.

## Available Templates

### 1. [FastAPI Starter](fastapi_starter/)
**Complete REST API template with sqlite-worker**

- ✅ Full CRUD operations
- ✅ Pydantic models for validation
- ✅ Automatic API documentation
- ✅ Production-ready structure

**Perfect for:** Web APIs, Microservices, Backend applications

```bash
cd fastapi_starter
pip install -r requirements.txt
python app.py
```

---

### 2. [Jupyter Notebook](jupyter_notebook/)
**Data analysis template with visualization**

- ✅ Pandas integration
- ✅ Data visualization examples
- ✅ Statistical analysis
- ✅ Export to CSV/Excel

**Perfect for:** Data analysis, Reporting, Research

```bash
cd jupyter_notebook
pip install -r requirements.txt
jupyter notebook data_analysis.ipynb
```

---

### 3. [CLI Tool](cli_tool/)
**Command-line interface template**

- ✅ CRUD operations via CLI
- ✅ JSON import/export
- ✅ Search and filter
- ✅ User-friendly interface

**Perfect for:** Command-line tools, Scripts, Admin utilities

```bash
cd cli_tool
pip install -r requirements.txt
python cli.py --help
```

---

## Quick Start

1. **Choose a template** that matches your needs
2. **Copy the template** to your project directory:
   ```bash
   cp -r templates/fastapi_starter my_project
   cd my_project
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Customize** the template for your use case
5. **Run** and start developing!

## Template Structure

Each template includes:
- 📝 **README.md** - Comprehensive documentation
- 🐍 **Python files** - Complete, working code
- 📦 **requirements.txt** - All dependencies
- 💡 **Examples** - Usage examples
- 🎨 **Customization guide** - How to adapt it

## Customization

All templates are designed to be easily customizable:

### Change Database Schema
```python
# Modify the initialization function
worker.execute("""
    CREATE TABLE your_table (
        id INTEGER PRIMARY KEY,
        your_field TEXT
    )
""")
```

### Add New Endpoints/Features
```python
# Add your business logic
def your_function():
    # Your code here
    pass
```

### Integrate with Your Stack
- Add authentication (JWT, OAuth)
- Integrate external APIs
- Add caching (Redis)
- Implement logging
- Add monitoring

## Use Cases by Template

### FastAPI Starter
- REST APIs
- Microservices
- Mobile app backends
- SaaS applications
- Internal tools

### Jupyter Notebook
- Data analysis
- Business intelligence
- Research projects
- Report generation
- Exploratory data analysis

### CLI Tool
- Database management
- Task automation
- System administration
- Data migration
- Development utilities

## Best Practices

When using templates:

1. **Read the README** - Each template has detailed documentation
2. **Understand the code** - Review before customizing
3. **Test thoroughly** - Ensure it works in your environment
4. **Add tests** - Write tests for your customizations
5. **Update dependencies** - Keep packages up to date
6. **Follow conventions** - Maintain code style

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/roshanlam/sqlite-worker/discussions)
- **Issues**: [Bug Reports](https://github.com/roshanlam/sqlite-worker/issues/new?template=bug_report.yml)
- **Examples**: Check [examples/](../examples/) for more use cases

## Contributing

Have a great template idea? We'd love to include it!

1. Create your template
2. Follow the existing template structure
3. Include comprehensive README
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Resources

- [Main Documentation](../ReadMe.md)
- [Examples Directory](../examples/)
- [Contributing Guide](../CONTRIBUTING.md)

## License

All templates are provided under the same license as sqlite-worker. See [LICENSE](../LICENSE) for details.

---

**Happy coding! 🎉**

Choose a template, customize it, and build something awesome with sqlite-worker!
