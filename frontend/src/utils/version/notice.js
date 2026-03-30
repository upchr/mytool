import {h} from "vue";
import {NButton} from "naive-ui";
import {formatDateNotice} from "@/utils/date.js";

const themeClassFont = () =>{
    if(window.$themeStore.isDark){
        return 'theme-dark-font'
    }
}
const themeClassBack = () =>{
    if(window.$themeStore.isDark){
        return 'theme-dark-back'
    }
}

export function notice(versionInfo,jump=false,jumpFunc=()=>{}) {
    let markAsRead = false

    const n = window.$notification.info({
        title: '升级提醒',
        content: () => {
            const links = [
                { url: 'https://github.com/upchr/FnDepot', text: 'GitHub - FnDepot' },
                { url: 'https://gitee.com/upchr/FnDepot', text: 'Gitee - FnDepot' },
                { url: 'https://github.com/upchr/mytool', text: 'GitHub - mytool' }
            ]

            return h('div',
                {
                    class: 'upgrade-notification',
                }, [
                // 版本信息
                h('div', { class: 'version-section' }, [
                    h('p', { class: `section-title ${themeClassFont()}` }, '版本信息'),
                    h('div', { class: 'version-info' }, [
                        h('div', { class: 'version-row' }, [
                            h('span', { class: `label ${themeClassFont()}` }, '最新版本：'),
                            h('span', { class: 'value newVersion' }, versionInfo.value.latest)
                        ]),
                        h('div', { class: 'version-row' }, [
                            h('span', { class: `label ${themeClassFont()}` }, '当前版本：'),
                            h('span', { class: 'value' }, versionInfo.value.current)
                        ])
                    ])
                ]),

                // Git 地址
                h('div', { class: 'links-section' }, [
                    h('p', { class: `section-title ${themeClassFont()}` }, '获取Git地址：'),
                    ...links.map(link =>
                        h('div', { class: 'link-item' }, [
                            h('a', {
                                href: link.url,
                                target: '_blank',
                                class: 'git-link',
                                onClick: (e) => {
                                    e.stopPropagation()
                                    window.open(link.url, '_blank')
                                }
                            }, link.text)
                        ])
                    )
                ]),

                // Docker 镜像
                h('div', { class: 'docker-section' }, [
                    h('p', { class: `section-title ${themeClassFont()}` }, '最新docker镜像：'),
                    h('div', { class: 'docker-image' }, [
                        h('code', { class: `docker-tag  ${themeClassBack()}`}, `chrplus/toolsplus:${versionInfo.value.latest}`),
                        h('button', {
                            class: `copy-btn  ${themeClassFont()}`,
                            onClick: (e) => {
                                window.$copyCode(`chrplus/toolsplus:${versionInfo.value.latest}`,e)
                                // handleCopy
                                /*e.stopPropagation()
                                navigator.clipboard.writeText(`chrplus/toolsplus:${versionInfo.value.latest}`)
                                window.$message.success('已复制到剪贴板')*/
                            }
                        }, '复制')
                    ])
                ]),

                // 提示信息
                jump ? h('div', { class: 'hint-section' }, [
                    h('p', { class: `section-title  ${themeClassFont()}` }, '应用升级'),
                    h('div', { class: '' }, [
                        h('div', { class: '' }, [
                            h('span', { class: `label ${themeClassFont()}` }, '可去"关于"菜单，查看详细说明。'),
                            h('button', {
                                class: `copy-btn ${themeClassFont()}`,
                                onClick: (e) => {
                                    e.stopPropagation()
                                    jumpFunc()  // 使用 goToAbout 函数
                                }
                            }, '关于')
                        ])
                    ])
                ]) : null
            ])
        },
        meta: formatDateNotice(versionInfo.value.updated_at),
        action: () => h(NButton, {
            text: true,
            type: 'primary',
            onClick: () => {
                markAsRead = true
                n.destroy()
            }
        }, { default: () => '已读' }),
        onClose: () => {
            if (!markAsRead) {
                window.$message.warning('请设为已读')
                return false
            }
        }
    })
}
