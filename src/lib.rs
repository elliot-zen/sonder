pub mod agent;
pub mod client;
pub mod completion;
pub mod providers;

pub use agent::{Agent, AgentBuilder};
pub use client::{Client, HttpClientExt};
pub use completion::{CompletionModel, CompletionRequest, CompletionResponse};

#[cfg(test)]
mod tests {
    use reqwest::header::AUTHORIZATION;

    use crate::{
        AgentBuilder, CompletionModel, HttpClientExt,
        client::{ClientBuiler, Provider, ProviderBuilder},
        providers::mock::{MockClient, MockCompletionModel},
    };

    #[derive(Debug, Clone)]
    struct ExampleExt {
        api_key: String,
    }

    #[derive(Debug, Clone)]
    struct ExampleExtBuilder;

    impl Provider for ExampleExt {
        type Builder = ExampleExtBuilder;
        const VERIFY_PATH: &'static str = "/models";

        fn with_custom(&self, req: reqwest::RequestBuilder) -> reqwest::RequestBuilder {
            req.bearer_auth(&self.api_key)
        }
    }

    impl ProviderBuilder for ExampleExtBuilder {
        type Extension<H>
            = ExampleExt
        where
            H: HttpClientExt;
        type ApiKey = String;
        const BASE_URL: &'static str = "https://api.example.com/v1";

        fn build<H>(self, api_key: Self::ApiKey) -> Self::Extension<H>
        where
            H: HttpClientExt,
        {
            ExampleExt { api_key }
        }
    }

    #[tokio::test]
    async fn client_builder_can_build_provider_client() -> anyhow::Result<()> {
        let client = ClientBuiler::new(ExampleExtBuilder, "test-key".to_string()).build();
        assert_eq!(client.base_url(), "https://api.example.com/v1");
        Ok(())
    }

    #[tokio::test]
    async fn provider_client_can_build_get_request() -> anyhow::Result<()> {
        let client = ClientBuiler::new(ExampleExtBuilder, "test-key".to_string()).build();
        let request = client.get("/models").build()?;
        assert_eq!(request.method(), reqwest::Method::GET);
        assert_eq!(request.url().as_str(), "https://api.example.com/v1/models");

        let auth = request.headers().get(AUTHORIZATION).unwrap().to_str()?;
        assert_eq!(auth, "Bearer test-key");
        Ok(())
    }

    #[tokio::test]
    async fn provider_client_can_build_post_request() -> anyhow::Result<()> {
        let client = ClientBuiler::new(ExampleExtBuilder, "test-key".to_string()).build();
        let request = client.post("/models").build()?;
        assert_eq!(request.method(), reqwest::Method::POST);
        assert_eq!(request.url().as_str(), "https://api.example.com/v1/models");

        let auth = request.headers().get(AUTHORIZATION).unwrap().to_str()?;
        assert_eq!(auth, "Bearer test-key");
        Ok(())
    }

    #[tokio::test]
    async fn agent_can_prompt_mock_model() -> anyhow::Result<()> {
        let model = MockCompletionModel::make(MockClient::new(), "mock-model");
        let agent = AgentBuilder::new(model)
            .preambel("You are helpful.")
            .build();

        let answer = agent.prompt("hello").await?;
        assert_eq!(answer, "preamble: You are helpful.\nmock response: hello");
        Ok(())
    }
}
