#[derive(Debug, Clone)]
pub struct CompletionRequest {
    pub prompt: String,
    pub preamble: Option<String>,
}

#[derive(Debug, Clone)]
pub struct CompletionResponse {
    pub text: String,
}
pub trait CompletionModel {
    type Client;

    fn make(client: Self::Client, model: impl Into<String>) -> Self;

    fn completion(&self, request: CompletionRequest) -> impl Future<Output = anyhow::Result<CompletionResponse>> + Send;
}
