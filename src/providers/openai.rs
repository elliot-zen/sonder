use anyhow::{Context, Ok};
use serde::{Deserialize, Serialize};

use crate::{
    CompletionModel, CompletionResponse, HttpClientExt,
    client::{
        self, BearerAuth, Capable, Capablities, Nothing, Provider, ProviderBuilder, ProviderClient,
    },
};

#[derive(Debug, Clone, Default)]
pub struct OpenAIExt;

#[derive(Debug, Clone, Default)]
pub struct OpenAIExtBuilder;

pub type Client<H = reqwest::Client> = client::Client<OpenAIExt, H>;
type OpenAIApiKey = BearerAuth;

impl Provider for OpenAIExt {
    type Builder = OpenAIExtBuilder;
    const VERIFY_PATH: &'static str = "/models";
}

impl ProviderBuilder for OpenAIExtBuilder {
    type Extension<H>
        = OpenAIExt
    where
        H: crate::HttpClientExt;
    type ApiKey = OpenAIApiKey;
    const BASE_URL: &'static str = "https://api.deepseek.com";

    fn build<H>(
        _client_builder: &client::ClientBuiler<Self, Self::ApiKey, H>,
    ) -> anyhow::Result<Self::Extension<H>>
    where
        H: HttpClientExt,
    {
        Ok(OpenAIExt)
    }
}

impl<H> Capablities<H> for OpenAIExt
where
    H: HttpClientExt,
{
    type Completion = Capable<OpenAiCompletionModel<H>>;
    type Embeddings = Nothing;
    type Transcription = Nothing;
    type ModelListing = Nothing;
}

pub struct OpenAiCompletionModel<H>
where
    H: HttpClientExt,
{
    client: client::Client<OpenAIExt, H>,
    model: String,
}

impl<H> CompletionModel for OpenAiCompletionModel<H>
where
    H: HttpClientExt,
{
    type Client = client::Client<OpenAIExt, H>;

    fn make(client: &Self::Client, model: impl Into<String>) -> Self {
        Self {
            client: client.clone(),
            model: model.into(),
        }
    }

    async fn completion(
        &self,
        request: crate::CompletionRequest,
    ) -> anyhow::Result<crate::CompletionResponse> {
        let mut messages = Vec::new();

        if let Some(preamble) = request.preamble {
            messages.push(ChatMessage {
                role: "system",
                content: preamble,
            });
        }

        messages.push(ChatMessage {
            role: "user",
            content: request.prompt,
        });

        let body = ChatCompletionRequest {
            model: self.model.clone(),
            messages,
        };

        let req = self.client.post("/chat/completions").json(&body).build()?;

        let resp = self.client.send(req).await?;
        let status = resp.status();
        let text = resp.text().await?;

        if !status.is_success() {
            anyhow::bail!(
                "openai-comatible request failed: status={}, body={}",
                status,
                text,
            )
        }

        let parsed: ChatCompletionResponse = serde_json::from_str(&text)?;
        let content = parsed
            .choices
            .into_iter()
            .next()
            .and_then(|choice| choice.message.content)
            .ok_or_else(|| anyhow::anyhow!("missing assistant messsage content;"))?;

        Ok(CompletionResponse { text: content })
    }
}

#[derive(Debug, Serialize)]
struct ChatCompletionRequest {
    model: String,
    messages: Vec<ChatMessage>,
}

#[derive(Debug, Serialize)]
struct ChatMessage {
    role: &'static str,
    content: String,
}

#[derive(Debug, Deserialize)]
struct ChatCompletionResponse {
    choices: Vec<ChatCompletionChoice>,
}

#[derive(Debug, Deserialize)]
struct ChatCompletionChoice {
    message: ChatCompletionMessage,
}

#[derive(Debug, Deserialize)]
struct ChatCompletionMessage {
    content: Option<String>,
}

impl ProviderClient for Client {
    type Input = OpenAIApiKey;
    type Error = anyhow::Error;

    fn from_env() -> anyhow::Result<Self, Self::Error> {
        let base_url = std::env::var("OPENAI_BASE_URL")
            .context("No `OPENAI_BASE_URL` environment variable set")?;
        let api_key = std::env::var("OPENAI_API_KEY")
            .context("No `OPENAI_API_KEY` environment variable set")?;
        let builder = Self::builder().base_url(base_url).api_key(api_key);
        builder.build()
    }

    fn from_val(input: Self::Input) -> anyhow::Result<Self, Self::Error> {
        Self::new(input).context("cannot create client from `input`")
    }
}
