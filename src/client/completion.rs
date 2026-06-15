use crate::{
    AgentBuilder, CompletionModel,
    client::{Capable, Capablities, Client},
};

pub trait CompletionClient {
    type CompletionModel: CompletionModel<Client = Self>;

    fn completion_model(&self, model: impl Into<String>) -> Self::CompletionModel;

    fn agent(&self, model: impl Into<String>) -> AgentBuilder<Self::CompletionModel> {
        let model = self.completion_model(model);
        AgentBuilder::new(model)
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
