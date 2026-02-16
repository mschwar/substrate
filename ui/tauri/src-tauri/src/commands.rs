#![allow(dead_code)]

use reqwest::blocking::Client;
use reqwest::header::HeaderMap;
use serde::{Deserialize, Serialize};
use std::env;

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

#[derive(Debug, Deserialize, Serialize)]
pub struct InboxParams {
    pub limit: Option<u32>,
    pub offset: Option<u32>,
    pub sort: Option<String>,
    pub status: Option<String>,
    pub privacy: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct SearchParams {
    pub query: String,
    pub limit: Option<u32>,
    pub offset: Option<u32>,
    pub status: Option<String>,
    pub privacy: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct CaptureParams {
    pub title: String,
    pub body: Option<String>,
    pub tags: Option<Vec<String>>,
    pub privacy: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct PromoteParams {
    pub path: String,
    pub status: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct ValidateParams {
    pub frontmatter: serde_json::Value,
    pub body: Option<String>,
    pub path: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct ItemUpdateParams {
    pub path: String,
    pub frontmatter: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub body: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub validate_only: Option<bool>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct DailyOpenParams {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub date: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct DailyAppendParams {
    pub text: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub date: Option<String>,
}

fn api_base() -> String {
    env::var("SUBSTRATE_API").unwrap_or_else(|_| "http://127.0.0.1:8123".to_string())
}

fn auth_header() -> Option<String> {
    env::var("SUBSTRATE_TOKEN").ok()
}

fn client() -> Client {
    Client::new()
}

fn add_auth(headers: &mut HeaderMap) {
    if let Some(token) = auth_header() {
        headers.insert("X-Substrate-Token", token.parse().unwrap());
    }
}

fn parse_response(resp: reqwest::blocking::Response) -> Result<serde_json::Value, CommandError> {
    if !resp.status().is_success() {
        let text = resp.text().unwrap_or_default();
        return Err(CommandError::new(&format!("api error: {text}")));
    }
    resp.json::<serde_json::Value>()
        .map_err(|_| CommandError::new("invalid api response"))
}

#[tauri::command]
pub fn inbox_view(params: InboxParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/inbox", api_base());
    let mut req = client().get(url);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);

    let mut query: Vec<(String, String)> = Vec::new();
    query.push(("limit".into(), params.limit.unwrap_or(20).to_string()));
    query.push(("offset".into(), params.offset.unwrap_or(0).to_string()));
    query.push(("sort".into(), params.sort.unwrap_or_else(|| "updated_desc".to_string())));
    if let Some(status) = params.status {
        query.push(("status".into(), status));
    }
    if let Some(privacy) = params.privacy {
        query.push(("privacy".into(), privacy));
    }
    let resp = req.query(&query).send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn item_view(path: String) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/item", api_base());
    let mut req = client().get(url);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req
        .query(&[("path", path)])
        .send()
        .map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn search(params: SearchParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/search", api_base());
    let mut req = client().get(url);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);

    let mut query: Vec<(String, String)> = Vec::new();
    query.push(("q".into(), params.query));
    query.push(("limit".into(), params.limit.unwrap_or(20).to_string()));
    query.push(("offset".into(), params.offset.unwrap_or(0).to_string()));
    if let Some(status) = params.status {
        query.push(("status".into(), status));
    }
    if let Some(privacy) = params.privacy {
        query.push(("privacy".into(), privacy));
    }
    let resp = req.query(&query).send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn capture(params: CaptureParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/capture", api_base());
    let mut req = client().post(url).json(&params);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req.send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn promote(params: PromoteParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/promote", api_base());
    let mut req = client().post(url).json(&params);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req.send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn validate(params: ValidateParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/validate", api_base());
    let mut req = client().post(url).json(&params);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req.send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn item_update(params: ItemUpdateParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/item/update", api_base());
    let mut req = client().post(url).json(&params);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req.send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn daily_open(params: DailyOpenParams) -> Result<serde_json::Value, CommandError> {
    let mut url = format!("{}/api/daily/open", api_base());
    if let Some(date) = params.date.as_deref() {
        if !date.is_empty() {
            url.push_str("?date=");
            url.push_str(date);
        }
    }
    let mut req = client().get(url);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req.send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}

#[tauri::command]
pub fn daily_append(params: DailyAppendParams) -> Result<serde_json::Value, CommandError> {
    let url = format!("{}/api/daily/append", api_base());
    let mut req = client().post(url).json(&params);
    let mut headers = HeaderMap::new();
    add_auth(&mut headers);
    req = req.headers(headers);
    let resp = req.send().map_err(|_| CommandError::new("api unreachable"))?;
    parse_response(resp)
}
