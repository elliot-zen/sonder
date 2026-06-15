use crate::{CompletionRequest, CompletionResponse};

pub trait CompletionModel {
    type Client;

    fn make(client: &Self::Client, model: impl Into<String>) -> Self;

    fn completion(&self, request: CompletionRequest) -> impl Future<Output = anyhow::Result<CompletionResponse>> + Send;
}
