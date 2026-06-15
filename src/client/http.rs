use anyhow::Context;
use reqwest::{Request, RequestBuilder, Response};

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
