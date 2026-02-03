#![allow(dead_code)]

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize)]
pub struct CommandError {
    pub message: String,
}

impl CommandError {
    pub fn new(message: &str) -> Self {
        Self {
            message: message.to_string(),
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct InboxParams {
    pub limit: Option<u32>,
    pub offset: Option<u32>,
    pub sort: Option<String>,
    pub status: Option<String>,
    pub privacy: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct SearchParams {
    pub query: String,
    pub limit: Option<u32>,
    pub offset: Option<u32>,
    pub status: Option<String>,
    pub privacy: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CaptureParams {
    pub title: String,
    pub body: Option<String>,
    pub tags: Option<Vec<String>>,
    pub privacy: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct PromoteParams {
    pub path: String,
    pub status: Option<String>,
}

fn invoke_bridge(command: &str, payload: serde_json::Value) -> Result<serde_json::Value, CommandError> {
    let payload_str = payload.to_string();
    let output = Command::new("python")
        .arg("tools/tauri_bridge.py")
        .arg(command)
        .arg(payload_str)
        .output()
        .map_err(|err| CommandError::new(&format!("bridge error: {err}")))?;

    if !output.status.success() {
        return Err(CommandError::new("bridge command failed"));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout).map_err(|_| CommandError::new("invalid bridge response"))
}

#[tauri::command]
pub fn inbox_view(params: InboxParams) -> Result<serde_json::Value, CommandError> {
    let payload = serde_json::to_value(params).map_err(|_| CommandError::new("invalid params"))?;
    invoke_bridge("inbox_view", payload)
}

#[tauri::command]
pub fn item_view(path: String) -> Result<serde_json::Value, CommandError> {
    let payload = serde_json::json!({"path": path});
    invoke_bridge("item_view", payload)
}

#[tauri::command]
pub fn search(params: SearchParams) -> Result<serde_json::Value, CommandError> {
    let payload = serde_json::to_value(params).map_err(|_| CommandError::new("invalid params"))?;
    invoke_bridge("search", payload)
}

#[tauri::command]
pub fn capture(params: CaptureParams) -> Result<serde_json::Value, CommandError> {
    let payload = serde_json::to_value(params).map_err(|_| CommandError::new("invalid params"))?;
    invoke_bridge("capture", payload)
}

#[tauri::command]
pub fn promote(params: PromoteParams) -> Result<serde_json::Value, CommandError> {
    let payload = serde_json::to_value(params).map_err(|_| CommandError::new("invalid params"))?;
    invoke_bridge("promote", payload)
}
