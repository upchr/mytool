用于更新应用对应fpk打包配置
- 自定义镜像fnpack-builder
- 传递版本变量VERSION
- 挂载最新打包配置
- 生成对应版本fpk安装包。
```bash
docker run --rm \
-e VERSION=${{ env.VERSION }} \
-v ${{ github.workspace }}/docker/fnfpk/toolsplus:/workspace/toolsplus \
-v /tmp/fnpack-workspace/files:/workspace/files \
chrplus/fnpack-builder:v1.2.0
```
