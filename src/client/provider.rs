use reqwest::RequestBuilder;

use crate::client::{ApiKey, ClientBuiler, HttpClientExt};

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


pub trait ProviderClient: Sized {
    type Input;
    type Error;

    fn from_env() -> anyhow::Result<Self, Self::Error>;

    fn from_val(input: Self::Input) -> anyhow::Result<Self, Self::Error>;
}
