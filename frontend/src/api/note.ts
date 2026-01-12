import axios from 'axios'

export const getNotes = () => axios.get('/notes')
export const createNote = (data: { title: string; content?: string }) => axios.post('/notes', data)
export const deleteNote = (data: { title: string; content?: string }) => axios.delete('/notes', data)
