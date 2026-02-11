import { defineStore } from 'pinia'

export const useLoginStore = defineStore('login', {
    state: () => ({
        showInitDialog: false,
        showLoginDialog: false
    }),
    actions: {
        openInitDialog() {
            this.showInitDialog = true
        },
        openLoginDialog() {
            this.showLoginDialog = true
        },
        closeInitDialog() {
            this.showInitDialog = false
        },
        closeLoginDialog() {
            this.showLoginDialog = false
        }
    }
})
