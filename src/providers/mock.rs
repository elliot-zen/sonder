use crate::completion::{CompletionModel, CompletionRequest, CompletionResponse};

#[derive(Debug, Clone)]
pub struct MockClient;

impl MockClient {
    pub fn new() -> Self {
        Self
    }
}

impl Default for MockClient {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone)]
pub struct MockCompletionModel {
    _client: MockClient,
    model: String,
}

impl MockCompletionModel {
    pub fn new() -> Self {
        Self {
            _client: MockClient::default(),
            model: "mock-model".to_string(),
        }
    }

    pub fn model_name(&self) -> &str {
        &self.model
    }
}

impl Default for MockCompletionModel {
    fn default() -> Self {
        MockCompletionModel::new()
    }
}

impl CompletionModel for MockCompletionModel {
    type Client = MockClient;

    fn make(client: Self::Client, model: impl Into<String>) -> Self {
        Self {
            _client: client,
            model: model.into(),
        }
    }

    async fn completion(&self, request: CompletionRequest) -> anyhow::Result<CompletionResponse> {
        let mut text = String::new();
        if let Some(preamble) = request.preamble {
            text.push_str("preamble: ");
            text.push_str(&preamble);
            text.push_str("\n");
        }
        text.push_str("mock response: ");
        text.push_str(&request.prompt);
        Ok(CompletionResponse { text })
    }
}
