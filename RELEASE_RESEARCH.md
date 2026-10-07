# GitHub Releases 发布调研

调研日期：2026-10-02。仅核实官方 GitHub 文档；没有创建远程发布。

- GitHub Releases 用于交付某个版本的软件、发布说明与下载附件。版本基于 Git 标签，可以将前端、后端作为同一个仓库版本发布，不需要拆成两个 Release。[About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- GitHub 自动提供标签对应仓库内容的 ZIP 和 tar.gz 源码下载。自行上传的附件可以是前端构建包、部署包、可执行程序等；自动生成的源码归档不会替项目完成构建或部署。[About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- 发布操作：仓库 → Releases → Draft a new release → 选择或创建标签 → 选择目标分支 → 填写标题和说明 → 上传附件 → Save draft 或 Publish release。可以将版本标记为预发布。若开启不可变发布，建议先以草稿上传全部附件，再发布。[Managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- Release 发布后的下载页面与线上应用托管是两个独立目标。GitHub Pages 属于静态 HTML/CSS/JavaScript 托管，因此它可以托管前端静态产物，但不能运行本项目的 FastAPI 服务；后端仍需运行在服务器或其他计算平台。这一后端结论是根据 Pages 的静态托管性质作出的判断。[What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

建议首版先提供清楚的源码安装说明、支持环境、功能范围和已知限制；若提供构建附件，应说明它需要配套后端与运行环境。是否称为 v1.0.0 或预览版，取决于实际完成度与兼容性承诺。
