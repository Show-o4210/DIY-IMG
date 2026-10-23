# 公共文本 icon 独立目录

**文本嵌入图标只放在本目录的 `items/`。禁止放入上一级 `public-assets/items/`。** 上一级普通素材接口继续服务旧版；新版客户端才请求本目录，不需要旧版适配。`SKILL` 英雄技能素材仍属于普通素材，不能与 `TEXT_ICON` 混用。

本目录已收录 **1 项**：**[破甲](items/text-icon-armor-break-khh/original.png)**，引用 **`[khh]`**。原图为 1254×1254 RGBA PNG，保持原始透明度、尺寸和字节；署名暂记“用户提供（作者未注明）”。发布入口为 `text-icons/catalog/index.json`（相对于 `public-assets/`）；索引和清单使用 `schema_version: 1`、`kind: "text-icons"`。`files/`、`catalog/manifests/`、`tags.json`、缓存及维护备份都与普通素材分开。

## 添加图标

推荐在公共素材维护工具的“更多操作 → 切换普通素材 / 文本图标目录”中操作。确认顶部路径为 `public-assets/text-icons`；表单分别填写“备注名”和“嵌入名”。工具默认生成唯一的 `pub_...` 嵌入名。

手工维护时，在 `items/<固定ID>/` 中放入原始 PNG / JPEG 和 `info.json`：

```json
{
  "id": "text-icon-show-frost-01",
  "category": "TEXT_ICON",
  "name": "冰冻效果·show",
  "embed_key": "pub_show_frost_01",
  "tags": [],
  "aliases": ["冻结", "霜冻"],
  "author": "show",
  "source_url": "https://example.org/replace-with-real-source",
  "usage": "请替换为作者实际许可范围",
  "description": "",
  "file": "original.png",
  "published_at": "2026-10-23T12:00:00+08:00"
}
```

`name` 是展示及默认备注，须为单行、最多 80 个 UTF-16 字符；`embed_key` 是 `[嵌入名]` 中的键，须满足 `[a-z][a-z0-9_-]{0,63}`，共 1–64 位；可手动使用 `khh` 这样的短名，工具仍默认生成 `pub_...` 唯一名。不得使用内置语法（如 `a`、`b`、`ice`）或保留文件名（如 `con`、`lpt1`）。备注可重名，嵌入名全库唯一；`aliases` 只用于搜索。原图保留字节，不裁切、不重编码。

**一旦生成过发布目录，固定 ID、嵌入名及图片内容即冻结。** 备注、标签、说明可改；换图请新建 ID 和嵌入名，下架也不释放旧键。不要删除历史 `files/` 或 `catalog/manifests/`。

资源仓库根目录命令：

```powershell
python scripts/build_public_assets.py --text-icons --build
python scripts/build_public_assets.py --text-icons
```

维护工具目录命令（`--workspace` 指向含 `public-assets` 的工作区或资源仓库）：

```powershell
python cli.py --workspace "F:/资源仓库/DIY-IMG" init-icons
python cli.py --workspace "F:/资源仓库/DIY-IMG" --text-icons add "C:/素材/冰冻.png" --name "冰冻效果" --embed-key pub_show_frost_01 --author show --usage "作者实际许可范围"
python cli.py --workspace "F:/资源仓库/DIY-IMG" --text-icons validate
python cli.py --workspace "F:/资源仓库/DIY-IMG" --text-icons generate
```

所有图标 `list/show/update/import/export/sync/backups/restore` 命令都必须带 `--text-icons`，或将工作区直接指向 `public-assets/text-icons`。图标发布包只能合并到本目录；不要覆盖普通素材的 items、tags 或索引。普通素材和图标分别同步、分别备份恢复。

## 客户端行为

入库按嵌入名建立语法，备注单独保存；个人备注优先于公共默认备注。相同内容复用时也登记图标语法。冲突不覆盖本地图标，用户可另填符合规则且未占用的本机嵌入名。未添加时只展示建议语法，添加成功后才复制有效本机语法；缓存哈希不会作为嵌入名。图标和有效备注随工程 / 素材包携带，离线可用。

开发构建可通过 `-PpublicTextIconsBaseUrl=...` 单独指定图标根地址；缺省为普通素材根地址追加 `/text-icons`。

新目录须随资源仓库发布脚本一起部署。仅在本地生成不代表已经上线；发布后的旧入口仍不包含 `TEXT_ICON`。
