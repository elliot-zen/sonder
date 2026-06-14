use anyhow::Context;
use reqwest::{
    Request, RequestBuilder, Response,
    header::{HeaderMap, HeaderName, HeaderValue},
};

pub trait HttpClientExt {
    fn get(&self, url: &str) -> RequestBuilder;
    fn post(&self, url: &str) -> RequestBuilder;
    fn send(&self, request: Request) -> impl Future<Output = anyhow::Result<Response>> + Send;
}

impl HttpClientExt for reqwest::Client {
    fn get(&self, url: &str) -> RequestBuilder {
        reqwest::Client::get(self, url)
    }

    fn post(&self, url: &str) -> RequestBuilder {
        reqwest::Client::post(self, url)
    }

    async fn send(&self, request: Request) -> anyhow::Result<Response> {
        self.execute(request)
            .await
            .context("failed execute request")
    }
}

#[derive(Debug)]
pub struct Client<Ext, H> {
    base_url: String,
    headers: HeaderMap,
    http_client: H,
    ext: Ext,
}

impl<Ext, H> Client<Ext, H>
where
    H: HttpClientExt,
{
    pub fn new(base_url: impl Into<String>, ext: Ext, http_client: H) -> Self {
        Self {
            base_url: base_url.into(),
            headers: HeaderMap::new(),
            http_client,
            ext,
        }
    }

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

#[derive(Debug, Clone)]
pub struct ClientBuiler<ExtBuider, Key, H> {
    base_url: String,
    headers: HeaderMap,
    api_key: Key,
    http_client: H,
    ext_builder: ExtBuider,
}

impl<ExtBuilder, Key> ClientBuiler<ExtBuilder, Key, reqwest::Client>
where
    ExtBuilder: ProviderBuilder<ApiKey = Key>,
{
    pub fn new(ext_builder: ExtBuilder, api_key: Key) -> Self {
        Self {
            base_url: ExtBuilder::BASE_URL.to_string(),
            headers: HeaderMap::new(),
            api_key,
            http_client: reqwest::Client::new(),
            ext_builder,
        }
    }
}

impl<ExtBuilder, Key, H> ClientBuiler<ExtBuilder, Key, H>
where
    ExtBuilder: ProviderBuilder<ApiKey = Key>,
    H: HttpClientExt,
{
    pub fn base_url(mut self, base_url: impl Into<String>) -> Self {
        self.base_url = base_url.into();
        self
    }

    pub fn header(mut self, name: HeaderName, value: HeaderValue) -> Self {
        self.headers.insert(name, value);
        self
    }

    pub fn http_client<NewH>(self, http_client: NewH) -> ClientBuiler<ExtBuilder, Key, NewH>
    where
        NewH: HttpClientExt,
    {
        ClientBuiler {
            base_url: self.base_url,
            headers: self.headers,
            api_key: self.api_key,
            http_client,
            ext_builder: self.ext_builder,
        }
    }

    pub fn build(self) -> Client<ExtBuilder::Extension<H>, H> {
        let ext = self.ext_builder.build::<H>(self.api_key);

        let mut client = Client::new(self.base_url, ext, self.http_client);
        *client.headers_mut() = self.headers;
        client
    }
}

pub trait Provider {
    type Builder: ProviderBuilder;
    const VERIFY_PATH: &'static str;

    fn build_url(&self, base_url: &str, path: &str) -> String {
        let base_url = base_url.trim_end_matches('/');
        let path = path.trim_start_matches('/');
        format!("{base_url}/{path}")
    }

    fn with_custom(&self, req: RequestBuilder) -> RequestBuilder {
        req
    }
}

pub trait ProviderBuilder {
    type Extension<H>: Provider<Builder = Self>
    where
        H: HttpClientExt;
    type ApiKey;
    const BASE_URL: &'static str;

    fn build<H>(self, api_key: Self::ApiKey) -> Self::Extension<H>
    where
        H: HttpClientExt;
}
