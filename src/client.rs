use std::marker::PhantomData;

use anyhow::{Context, Ok};
use reqwest::{
    Request, RequestBuilder, Response,
    header::{HeaderMap, HeaderName, HeaderValue},
};

use crate::{AgentBuilder, CompletionModel, http_client};

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

pub trait HttpClientExt: Clone + Send + Sync {
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

impl<M, Ext, H> CompletionClient for Client<Ext, H>
where
    Ext: Capablities<H, Completion = Capable<M>>,
    M: CompletionModel<Client = Self>,
{
    type CompletionModel = M;

    fn completion_model(&self, model: impl Into<String>) -> Self::CompletionModel {
        M::make(self, model)
    }
}

#[derive(Debug, Clone)]
pub struct ClientBuiler<ExtBuider, Key = Missing, H = Missing> {
    base_url: String,
    headers: HeaderMap,
    api_key: Key,
    http_client: H,
    ext_builder: ExtBuider,
}

impl<ExtBuilder> Default for ClientBuiler<ExtBuilder, Missing, Missing>
where
    ExtBuilder: ProviderBuilder + Default,
{
    fn default() -> Self {
        Self {
            base_url: ExtBuilder::BASE_URL.to_string(),
            headers: HeaderMap::new(),
            api_key: Missing,
            http_client: Missing,
            ext_builder: ExtBuilder::default(),
        }
    }
}

impl<ExtBuider, H> ClientBuiler<ExtBuider, Missing, H> {
    pub fn api_key<Key>(self, api_key: impl Into<Key>) -> ClientBuiler<ExtBuider, Key, H> {
        ClientBuiler {
            api_key: api_key.into(),
            base_url: self.base_url,
            headers: self.headers,
            http_client: self.http_client,
            ext_builder: self.ext_builder,
        }
    }
}

impl<ExtBuider, Key, H> ClientBuiler<ExtBuider, Key, H> {
    pub fn base_url<S>(self, base_url: S) -> Self
    where
        S: AsRef<str>,
    {
        Self {
            base_url: base_url.as_ref().to_string(),
            ..self
        }
    }
    pub fn http_client<U>(self, http_client: U) -> ClientBuiler<ExtBuider, Key, U> {
        ClientBuiler {
            http_client,
            base_url: self.base_url,
            headers: self.headers,
            api_key: self.api_key,
            ext_builder: self.ext_builder,
        }
    }
}

impl<ExtBuilder, Key> ClientBuiler<ExtBuilder, Key, Missing>
where
    ExtBuilder: ProviderBuilder<ApiKey = Key>,
    Key: ApiKey,
{
    pub fn build(
        self,
    ) -> anyhow::Result<Client<ExtBuilder::Extension<reqwest::Client>, reqwest::Client>> {
        self.http_client(reqwest::Client::new()).build()
    }
}

impl<ExtBuider, Key, H> ClientBuiler<ExtBuider, Key, H>
where
    ExtBuider: ProviderBuilder<ApiKey = Key>,
    Key: ApiKey,
    H: HttpClientExt,
{
    pub fn build(self) -> anyhow::Result<Client<ExtBuider::Extension<H>, H>> {
        // let ext_builder = self.ext_builder.clone();
        let ext = ExtBuider::build(&self)?;
        let ClientBuiler {
            api_key,
            base_url,
            http_client,
            mut headers,
            ..
        } = self;

        if let Some((k, v)) = api_key.into_header().transpose()?
            && !headers.contains_key(&k)
        {
            headers.insert(k, v);
        }
        Ok(Client {
            base_url,
            http_client,
            headers,
            ext,
        })
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

pub trait ProviderBuilder: Sized + Default + Clone {
    type Extension<H>: Provider<Builder = Self>
    where
        H: HttpClientExt;
    type ApiKey: ApiKey;
    const BASE_URL: &'static str;

    fn build<H>(
        client_builder: &ClientBuiler<Self, Self::ApiKey, H>,
    ) -> anyhow::Result<Self::Extension<H>>
    where
        H: HttpClientExt;
}

#[derive(Debug, Clone)]
pub struct Capable<M>(PhantomData<M>);

#[derive(Debug, Clone)]
pub struct Nothing;

#[derive(Debug, Clone)]
pub struct Missing;

pub trait Capablities<H>: Provider {
    type Completion;
    type Embeddings;
    type Transcription;
    type ModelListing;
}

pub trait CompletionClient {
    type CompletionModel: CompletionModel<Client = Self>;

    fn completion_model(&self, model: impl Into<String>) -> Self::CompletionModel;

    fn agent(&self, model: impl Into<String>) -> AgentBuilder<Self::CompletionModel> {
        let model = self.completion_model(model);
        AgentBuilder::new(model)
    }
}

pub trait ProviderClient: Sized {
    type Input;
    type Error;

    fn from_env() -> anyhow::Result<Self, Self::Error>;

    fn from_val(input: Self::Input) -> anyhow::Result<Self, Self::Error>;
}
