mod builder;
mod capability;
mod completion;
mod http;
mod provider;

pub use builder::ClientBuiler;
pub use capability::{Capable, Capablities};
pub use completion::CompletionClient;
pub use http::HttpClientExt;
pub use provider::{Provider, ProviderBuilder, ProviderClient};

use crate::http_client;
use reqwest::{
    Request, RequestBuilder, Response,
    header::{HeaderMap, HeaderName, HeaderValue},
};

#[derive(Debug, Clone)]
pub struct Nothing;

#[derive(Debug, Clone)]
pub struct Missing;

pub trait ApiKey: Sized {
    fn into_header(self) -> Option<anyhow::Result<(HeaderName, HeaderValue)>> {
        None
    }
}

pub struct BearerAuth(String);

impl<S> From<S> for BearerAuth
where
    S: Into<String>,
{
    fn from(value: S) -> Self {
        Self(value.into())
    }
}

impl ApiKey for BearerAuth {
    fn into_header(self) -> Option<anyhow::Result<(HeaderName, HeaderValue)>> {
        Some(http_client::make_auth_header(self.0))
    }
}

#[derive(Debug, Clone)]
pub struct Client<Ext, H> {
    base_url: String,
    headers: HeaderMap,
    http_client: H,
    ext: Ext,
}
impl<Ext> Client<Ext, reqwest::Client>
where
    Ext: Provider,
    Ext::Builder: ProviderBuilder<Extension<reqwest::Client> = Ext>,
{
    pub fn new(
        api_key: impl Into<<Ext::Builder as ProviderBuilder>::ApiKey>,
    ) -> anyhow::Result<Self> {
        Self::builder().api_key(api_key).build()
    }
}

impl<Ext, H> Client<Ext, H>
where
    H: HttpClientExt,
{
    pub fn base_url(&self) -> &str {
        return &self.base_url;
    }

    pub fn headers(&self) -> &HeaderMap {
        return &self.headers;
    }

    pub fn headers_mut(&mut self) -> &mut HeaderMap {
        return &mut self.headers;
    }

    pub fn http_client(&self) -> &H {
        &self.http_client
    }

    pub fn with_ext<NewExt>(self, ext: NewExt) -> Client<NewExt, H> {
        Client {
            base_url: self.base_url,
            headers: self.headers,
            http_client: self.http_client,
            ext,
        }
    }

    pub async fn send(&self, request: Request) -> anyhow::Result<Response> {
        self.http_client.send(request).await
    }
}
impl<Ext> Client<Ext, reqwest::Client>
where
    Ext: Provider,
    Ext::Builder: ProviderBuilder + Default,
{
    pub fn builder() -> ClientBuiler<Ext::Builder, Missing, Missing> {
        ClientBuiler::default()
    }
}

impl<Ext, H> Client<Ext, H>
where
    Ext: Provider,
    H: HttpClientExt,
{
    pub fn get(&self, path: &str) -> RequestBuilder {
        let url = self.ext.build_url(&self.base_url, path);
        let req = self.http_client.get(&url).headers(self.headers.clone());
        self.ext.with_custom(req)
    }

    pub fn post(&self, path: &str) -> RequestBuilder {
        let url = self.ext.build_url(&self.base_url, path);
        let req = self.http_client.post(&url).headers(self.headers.clone());
        self.ext.with_custom(req)
    }
}
