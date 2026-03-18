
import tkinter as tk
from db import add_user

def launch_register():

    root=tk.Tk()
    root.title("ユーザー登録")

    tk.Label(root,text="カードUID").grid(row=0,column=0)
    tk.Label(root,text="Cybozu ID").grid(row=1,column=0)
    tk.Label(root,text="Password").grid(row=2,column=0)

    uid=tk.Entry(root,width=30)
    userid=tk.Entry(root,width=30)
    password=tk.Entry(root,width=30,show="*")

    uid.grid(row=0,column=1)
    userid.grid(row=1,column=1)
    password.grid(row=2,column=1)

    status=tk.Label(root,text="")
    status.grid(row=4,columnspan=2)

    def save():
        add_user(uid.get(),userid.get(),password.get())
        status.config(text="登録完了")

    tk.Button(root,text="登録",command=save).grid(row=3,columnspan=2)

    root.mainloop()
