#![allow(dead_code)]

mod commands;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::inbox_view,
            commands::item_view,
            commands::search,
            commands::capture,
            commands::promote,
            commands::validate,
            commands::item_update,
            commands::daily_open,
            commands::daily_append,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
