use reqwest::header::{HeaderName, HeaderValue};

pub fn make_auth_header(key: impl AsRef<str>) -> anyhow::Result<(HeaderName, HeaderValue)> {
    Ok((
        reqwest::header::AUTHORIZATION,
        HeaderValue::from_str(&format!("Bearer {}", key.as_ref()))?,
    ))
}
