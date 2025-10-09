from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.core.utils import verify_admin
import uuid
import asyncio
import json

router = APIRouter()

plugin_ws = None
pending_requests = {}
dashboard_clients = []

pending_logs: list[str] = []
MAX_LOGS = 500

def add_log(log_message: str):
    pending_logs.append(log_message)
    if len(pending_logs) > MAX_LOGS:
        pending_logs.pop(0)


@router.websocket("/ws")
async def ws(websocket: WebSocket):
    global plugin_ws
    await websocket.accept()
    await websocket.send_text("{\"message\": \"Connected!\"}")
    plugin_ws = websocket
    try:

        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)

            if "log" in json_data:
                log_message = json_data["log"]
                add_log(log_message)

                # Forward to dashboards
                for ws in list(dashboard_clients):
                    try:
                        await ws.send_text(json.dumps({"log": log_message}))
                    except:
                        dashboard_clients.remove(ws)

            request_id = json_data.get("request_id")
            response = json_data.get("response")
            if request_id in pending_requests:
                fut = pending_requests.pop(request_id)
                fut.set_result(response)                                                                                                                                                       

    except WebSocketDisconnect:
        print("Websocket disconnected")
        plugin_ws = None

@router.websocket("/ws/server_logs")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    for log in pending_logs:
        await websocket.send_text(json.dumps({"log": log}))

    dashboard_clients.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_clients.remove(websocket)


async def send_request_to_plugin(request_data):
    if plugin_ws is None:
        raise Exception("No plugin connected")

    request_id = str(uuid.uuid4())
    request_data["request_id"] = request_id
    fut = asyncio.get_event_loop().create_future()
    pending_requests[request_id] = fut

    await plugin_ws.send_text(json.dumps(request_data))

    try:
        response = await asyncio.wait_for(fut, timeout=30.0)
        return response
    
    except asyncio.TimeoutError:
        pending_requests.pop(request_id, None)
        raise Exception("Request timed out")

@router.post("/get-server-ip")
async def reveal_ip():
    try:
        response = await send_request_to_plugin({"action": "get_ip"})
        return {"status": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/player-count")
async def player_count():
    try:
        response = await send_request_to_plugin({"action": "get_player_count"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-server-stats")
async def server_stats():
    try:
        response = await send_request_to_plugin({"action": "get_server_stats"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mc/status")
async def get_mc_status(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        response = await send_request_to_plugin({"action": "get_status"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/start")
async def start_mc_server(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        response = await send_request_to_plugin({"action": "start_server"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/stop")
async def stop_mc_server(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "stop_server"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mc/restart")
async def restart_mc_server(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "restart_server"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/command")
async def send_mc_command(admin_id: str, command: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "send_command", "command": command})
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/mc/players")
async def get_mc_players(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "get_players"})
        return {"players": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/mc/whitelist/get")
async def add_mc_whitelist(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "get_whitelist"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/whitelist/add")
async def add_mc_whitelist(admin_id: str, player: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "add_whitelist", "player": player})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mc/whitelist/remove")
async def remove_mc_whitelist(admin_id: str, player: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "remove_whitelist", "player": player})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mc/whitelist/enable")
async def enable_mc_whitelist(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "enable_whitelist"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mc/whitelist/disable")
async def disable_mc_whitelist(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "disable_whitelist"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/backup")
async def backup_mc_server(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "backup_server"})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/mc/backups")
async def list_mc_backups(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "list_backups"})
        return {"backups": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mc/op/remove")
async def add_mc_op(admin_id: str, player: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "remove_op", "player": player})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/mc/player-data/delete")
async def get_mc_whitelist(admin_id: str, player: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try: 
        response = await send_request_to_plugin({"action": "delete_player", "player": player})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mc/server-properties/update")
async def update_mc_server_properties(admin_id: str, new_properties: dict):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "update_server_properties", "new_properties": new_properties})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mc/server-properties/get")
async def get_mc_server_properties(admin_id: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "get_server_properties"})
        return {"server_properties": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/world/backup")
async def backup_mc_world(admin_id: str, world_name: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "backup_world", "world_name": world_name})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/mc/world/backups")
async def list_mc_world_backups(admin_id: str, world_name: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "list_world_backups", "world_name": world_name})
        return {"backups": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/world/restore")
async def restore_mc_world(admin_id: str, world_name: str, backup_name: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        response = await send_request_to_plugin({"action": "restore_world", "world_name": world_name, "backup_name": backup_name})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/mc/player-data/modify")
async def modify_mc_player_data(admin_id: str, player: str, new_data: dict):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        response = await send_request_to_plugin({"action": "update_player", "player": player, "new_data": new_data})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/mc/player-data/delete")
async def delete_mc_player_data(admin_id: str, player: str):
    if verify_admin(admin_id) is False:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        response = await send_request_to_plugin({"action": "delete_player", "player": player})
        return {"status": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

