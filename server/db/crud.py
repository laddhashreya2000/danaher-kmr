from sqlalchemy.orm import Session
import os
import datetime
from . import models, schemas

#####################################
############ User-related ###########
#####################################

def get_user_by_email(db: Session, email_id: str):
    return db.query(models.User).filter(models.User.email_id == email_id).first()

def get_user_by_id(db: Session, id: int):
    return db.query(models.User).filter(models.User.id == id).first()

def create_user(db: Session, user: schemas.UserRegister):
    db_user = models.User(
        name=user.name, 
        passwd_hashed=user.passwd_hashed, 
        op_co=user.op_co,
        email_id=user.email_id,
        contact_no=user.contact_no
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_passwd(db: Session, email_id: str, new_passwd_hashed: str):
    db.query(models.User).filter(models.User.email_id==email_id).update({models.User.passwd_hashwd: new_passwd_hashed})
    db.commit()
    db_user = db.query(models.User).filter(models.User.email_id == email_id).first()
    return db_user

def update_user_info(db: Session, user: schemas.UserInfo):
    db.query(models.User).filter(models.User.id==user.id).update({models.User.op_co: user.op_co, models.User.contact_no: user.contact_no})
    db.commit()
    db_user = db.query(models.User).filter(models.User.id==user.id).first()
    return db_user


############################################
########### Folder & file-related ##########
############################################

def get_file_by_id(db: Session, id: str):
    return db.query(models.File).filter(models.File.id == id).first()


def get_file_by_name_in_parent(db: Session, name: str, parent: str):
    return db.query(models.File).filter(models.File.name == name, models.File.is_folder == False, models.File.parent == parent, models.File.in_trash == False).first()


def get_folder_by_name_in_parent(db: Session, name: str, parent: str):
    return db.query(models.File).filter(models.File.name == name, models.File.is_folder == True, models.File.parent == parent, models.File.in_trash == False).first()


# def get_folders_by_creator(db: Session, created_by: str):
#     return db.query(models.File).filter(models.File.created_by == created_by, models.File.in_trash == False).all()

def create_file(db: Session, f: schemas.FileCreate):
    db_file = models.File(
        name=f.name,
        abs_path=f.abs_path,
        is_folder=f.is_folder,
        parent=f.parent,
        created_by=f.created_by,
        created_on=f.created_on
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def update_folder_name(db: Session, folder: schemas.FileRename):
    original_folder = db.query(models.File).filter(models.File.id==folder.id, models.File.is_folder==True, models.File.in_trash==False).first()
    original_name = original_folder.name
    new_abs_path = original_folder.abs_path.replace(f"/{original_name}", f"/{folder.new_name}")
    db.query(models.File).filter(models.File.id==folder.id, models.File.is_folder==True, models.File.in_trash==False).update({models.File.name: folder.new_name, models.File.abs_path: new_abs_path})
    db.commit()

    # Update the absolute paths of all children & sub-children of the folder
    parents_to_check = [folder.id]
    while parents_to_check:
        parent_id = parents_to_check.pop(0)
        children_folder_ids = db.query(models.File.id).filter(models.File.parent==parent_id, models.File.is_folder==True).all()
        parents_to_check.extend([id for id, in children_folder_ids])
        for f in db.query(models.File).filter(models.File.parent==parent_id).all():
            new_abs_path = f.abs_path.replace(f"/{original_name}/", f"/{folder.new_name}/")
            print(f.id, f.name, new_abs_path)
            db.query(models.File).filter(models.File.parent==parent_id).update({models.File.abs_path: new_abs_path})
            db.commit()

    db_folder = db.query(models.File).filter(models.File.id==folder.id).first()
    return db_folder

def add_file_to_trash(db: Session, id: int):
    to_be_deleted_on = datetime.date.today()+datetime.timedelta(days=10)
    # Add file with specified id to trash
    db.query(models.File).filter(models.File.id==id, models.File.is_file==True, models.File.in_trash==False).update({models.File.in_trash: True, models.File.delete_on: to_be_deleted_on})
    db.commit()
    return {"id": id, "status": "added to trash"}

def add_folder_to_trash(db: Session, id: int):
    to_be_deleted_on = datetime.date.today()+datetime.timedelta(days=10)
    # Add folder with specified id to trash
    db.query(models.File).filter(models.File.id==id, models.File.is_folder==True, models.File.in_trash==False).update({models.File.in_trash: True, models.File.delete_on: to_be_deleted_on})
    db.commit()

    # Add contents of folder with specified id to trash
    parents_to_check = [id]
    while parents_to_check:
        parent_id = parents_to_check.pop(0)
        children_folder_ids = db.query(models.File.id).filter(models.File.parent==parent_id, models.File.is_folder==True, models.File.in_trash==False).all()
        parents_to_check.extend([id for id, in children_folder_ids])
        db.query(models.File).filter(models.File.parent==parent_id, models.File.in_trash==False).update({models.File.in_trash: True, models.File.delete_on: to_be_deleted_on})
        db.commit()
    return {"id": id, "status": "added to trash"}

def restore_file_from_trash(db: Session, id: int):
    # Restore folder with specified id from trash
    db.query(models.File).filter(models.File.id==id, models.File.is_folder==False, models.File.in_trash==True).update({models.File.in_trash: False, models.File.delete_on: None})
    db.commit()
    return {"id": id, "status": "removed from trash"}

def restore_folder_from_trash(db: Session, id: int):
    # Restore folder with specified id from trash
    db.query(models.File).filter(models.File.id==id, models.File.is_folder==True, models.File.in_trash==True).update({models.File.in_trash: False, models.File.delete_on: None})
    db.commit()

    # Restore contents of folder with specified id from trash
    parents_to_check = [id]
    while parents_to_check:
        parent_id = parents_to_check.pop(0)
        children_folder_ids = db.query(models.File.id).filter(models.File.parent==parent_id, models.File.is_folder==True, models.File.in_trash==True).all()
        parents_to_check.extend([id for id, in children_folder_ids])
        db.query(models.File).filter(models.File.parent==parent_id, models.File.in_trash==True).update({models.File.in_trash: False, models.File.delete_on: None})
        db.commit()
    return {"id": id, "status": "restored from trash"}