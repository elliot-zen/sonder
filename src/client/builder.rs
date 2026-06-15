use reqwest::header::HeaderMap;

use crate::client::{ApiKey, Client, HttpClientExt, Missing, ProviderBuilder};

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
