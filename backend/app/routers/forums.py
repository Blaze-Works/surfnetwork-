# app/routers/forums.py

from fastapi import APIRouter, HTTPException
from app.core.db import db
from app.core.utils import User, generate_uuid, time_elasped_string
from app.models.forum_model import Forum, ForumMessage, ForumSubmission, ForumReplySubmission
from datetime import datetime
import uuid
from typing import Any, Dict, List

router = APIRouter()

@router.put(path="/submit-forum", response_model=dict)
def submit_forum(forum_submission: ForumSubmission):
    forum_data = Forum(
        id = generate_uuid(),
        topic = forum_submission.title,
        author = forum_submission.user_id,
        content = forum_submission.content,
        time = datetime.now().isoformat(),
        replies = []
    )

    try:
        doc = db.collection("forums").document(forum_submission.category).get()
        category = doc.to_dict() or {"topics": [], "replies": []}
        topics : List[Dict[str, Any]]  = category.get("topics") or []

        for topic in topics:
            if (topic.get("title") == forum_submission.title and 
                topic.get("author") == forum_submission.user_id):
                raise HTTPException(status_code=400, detail={"error": "Duplicate forum submission detected."})

        topics.append(forum_data.dict())
        category["topics"] = topics
        db.collection("forums").document(forum_submission.category).set(category)
        return {"message": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.put(path="/submit-forum-reply", response_model=dict)
def submit_forum_reply(forum_reply_submission: ForumReplySubmission):
    forum_reply = ForumMessage(
        id = generate_uuid(),
        parent_id = forum_reply_submission.parent_id,
        author = forum_reply_submission.user_id,
        content = forum_reply_submission.content,
        time = datetime.now(),
        replies = []
    )

    try:
        doc = db.collection("forums").document(forum_reply_submission.category).get()
        category = doc.to_dict() or {"topics": [], "replies": []}
        replies_list: List[Dict[str, Any]] = category.get("replies", []) or []
        topics : List[Dict[str, Any]] = category.get("topics") or []

        for reply in replies_list:
            if (reply.get("parent_id") == forum_reply_submission.parent_id and
                reply.get("author") == forum_reply_submission.user_id and
                reply.get("content") == forum_reply_submission.content):
                raise HTTPException(status_code=400, detail={"error": "Duplicate forum reply detected."})

            if (reply.get("id") == forum_reply_submission.parent_id):
                reply["replies"].append(fetch_forum.id)

        for topic in topics:
            if (topic.get("id") == forum_reply_submission.parent_id):
                topic["replies"].append(forum_reply.id)

        replies_list.append(forum_reply.dict())
        category["replies"] = replies_list
        category["topics"] = topics
        db.collection("forums").document(forum_reply_submission.category).set(category)
        return {"message": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get(path="/fetch-forum", response_model=dict)
def fetch_forum():
    forum_content = {}
    categories = {}
    docs = db.collection("forums").stream()

    def parse_category(categories: Dict[str, Any], category_name: str) -> Any:
        category = categories.get(category_name, {"topics": []})
        topics: List[Dict[str, Any]] = category.get("topics", []) or []
        parsed_topics = []

        for topic in topics:
            user = User()
            user.fromUUID(str(topic.get("author")))
            topic["author"] = user.fetch_userdata().username
            topic["time"] = time_elasped_string(_format_time(topic.get("time")))
            topic["replies"] = len(topic.get("replies"))
            parsed_topics.append(topic)

        return parsed_topics

    for doc in docs:
        categories[doc.id] = doc.to_dict()
        forum_content[doc.id] = parse_category(categories, doc.id)
    
    return forum_content

@router.get(path="/fetch-forum/{category_name}", response_model=dict)
def fetch_forum_category(category_name: str):
    pages = fetch_forum().get(category_name, [])
        
    return {"pages": pages}

@router.get(path="/fetch-forum/{category_name}/{forum_id}", response_model=dict)
def fetch_forum_category(category_name: str, forum_id: str):
    doc = db.collection("forums").document(category_name).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

    category = doc.to_dict() or {}
    topics: List[Dict[str, Any]] = category.get("topics", []) or []
    replies_list: List[Dict[str, Any]] = category.get("replies", []) or []

    topic = next((t for t in topics if str(t.get("id")) == str(forum_id)), None)
    if topic is None:
        raise HTTPException(status_code=404, detail={"error": f"Forum id '{forum_id}' not found in category '{category_name}'"})

    replies_by_id: Dict[str, Dict[str, Any]] = {}
    children_map: Dict[str, List[Dict[str, Any]]] = {}

    for r in replies_list:
        rid = str(r.get("id"))
        replies_by_id[rid] = r.copy()
        parent = r.get("parent_id")
        if parent is None:
            parent_key = "root"
        else:
            parent_key = str(parent)
        
        children_map.setdefault(parent_key, []).append(r)

    def build_reply_tree(reply_obj: ForumMessage) -> ForumMessage:
        rid = str(reply_obj.get("id"))

        user = User()
        user.fromUUID(str(reply_obj.get("author")))

        node = ForumMessage(
            id = rid,
            parent_id = reply_obj.get("parent_id"),
            author = user.fetch_userdata().username,
            content = reply_obj.get("content"),
            time = time_elasped_string(_format_time(reply_obj.get("time"))),
            likes = reply_obj.get("likes", 0),
            dislikes = reply_obj.get("dislikes", 0),
            replies = []
        )

        children = children_map.get(rid, [])
        children_sorted = sorted(children, key=lambda x: (_to_datetime(x.get("time")) or datetime.fromtimestamp(0)))
        for child in children_sorted:
            node.replies.append(build_reply_tree(child))
        return node

    user = User()
    user.fromUUID(str(topic.get("author")))

    forum_page = Forum(
        id = str(topic.get("id")),
        topic = topic.get("topic"),
        author = user.fetch_userdata().username,
        content = topic.get("content"),
        time = time_elasped_string(_format_time(topic.get("time"))),
        likes = topic.get("likes", 0),
        dislikes = topic.get("dislikes", 0),
        replies = []
    )

    root_children = children_map.get(str(forum_id), [])
    root_sorted = sorted(root_children, key=lambda x: (_to_datetime(x.get("time")) or datetime.fromtimestamp(0)))
    for r in root_sorted:
        forum_page.replies.append(build_reply_tree(r))

    return {"forum_page": forum_page}

def _to_datetime(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
        
    try:
        if hasattr(val, "to_datetime"):
            return val.to_datetime()
        if hasattr(val, "ToDatetime"):
            return val.ToDatetime()
        if hasattr(val, "seconds") and hasattr(val, "nanos"):
            return datetime.fromtimestamp(val.seconds + val.nanos / 1e9)

    except Exception:
        pass

    try:
        return datetime.fromisoformat(str(val))
    except Exception: 
        return None

def _format_time(val):
    dt = _to_datetime(val)
    return dt.isoformat() if dt is not None else None

@router.put(path="/fetch-forum/{category_name}/{forum_id}/like", response_model=dict)
def like_forum(category_name: str, forum_id: str):
    doc = db.collection("forums").document(category_name).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

    category = doc.to_dict() or {}
    topics: List[Dict[str, Any]] = category.get("topics", []) or []

    topic = next((t for t in topics if str(t.get("id")) == str(forum_id)), None)
    if topic is None:
        raise HTTPException(status_code=404, detail={"error": f"Forum id '{forum_id}' not found in category '{category_name}'"})

    current_likes = topic.get("likes", 0) or 0
    try:
        current_likes = int(current_likes)
    except Exception:
        current_likes = 0

    topic["likes"] = current_likes + 1
    category["topics"] = topics
    db.collection("forums").document(category_name).set(category)

    return {"message": "success", "likes": topic["likes"]}

@router.put(path="/fetch-forum/{category_name}/{reply_id}/like-reply", response_model=dict)
def like_reply(category_name: str, reply_id: str):
    doc = db.collection("forums").document(category_name).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

    category = doc.to_dict() or {}
    replies: List[Dict[str, Any]] = category.get("replies", []) or []

    reply = next((t for t in replies if str(t.get("id")) == str(reply_id)), None)
    if reply is None:
        raise HTTPException(status_code=404, detail={"error": f"Reply id '{reply_id}' not found in category '{category_name}'"})

    current_likes = reply.get("likes", 0) or 0
    try:
        current_likes = int(current_likes)
    except Exception:
        current_likes = 0

    reply["likes"] = current_likes + 1
    category["replies"] = replies
    db.collection("forums").document(category_name).set(category)

    return {"message": "success", "likes": reply["likes"]}
    
@router.put(path="/fetch-forum/{category_name}/{forum_id}/dislike", response_model=dict)
def dislike_forum(category_name: str, forum_id: str):
    doc = db.collection("forums").document(category_name).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

    category = doc.to_dict() or {}
    topics: List[Dict[str, Any]] = category.get("topics", []) or []

    topic = next((t for t in topics if str(t.get("id")) == str(forum_id)), None)
    if topic is None:
        raise HTTPException(status_code=404, detail={"error": f"Forum id '{forum_id}' not found in category '{category_name}'"})

    current_dislikes = topic.get("dislikes", 0) or 0
    try:
        current_dislikes = int(current_dislikes)
    except Exception:
        current_dislikes = 0

    topic["dislikes"] = current_dislikes + 1
    category["topics"] = topics
    db.collection("forums").document(category_name).set(category)

    return {"message": "success", "dislikes": topic["dislikes"]}

@router.put(path="/fetch-forum/{category_name}/{reply_id}/dislike-reply", response_model=dict)
def dislike_reply(category_name: str, reply_id: str):
    doc = db.collection("forums").document(category_name).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

    category = doc.to_dict() or {}
    replies: List[Dict[str, Any]] = category.get("replies", []) or []

    reply = next((t for t in replies if str(t.get("id")) == str(reply_id)), None)
    if reply is None:
        raise HTTPException(status_code=404, detail={"error": f"Reply id '{reply_id}' not found in category '{category_name}'"})

    current_dislikes = reply.get("dislikes", 0) or 0
    try:
        current_dislikes = int(current_dislikes)
    except Exception:
        current_dislikes = 0

    reply["dislikes"] = current_dislikes + 1
    category["replies"] = replies
    db.collection("forums").document(category_name).set(category)

    return {"message": "success", "dislikes": reply["dislikes"]}