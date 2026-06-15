use std::marker::PhantomData;

use crate::client::Provider;

#[derive(Debug, Clone)]
pub struct Capable<M>(PhantomData<M>);

pub trait Capablities<H>: Provider {
    type Completion;
    type Embeddings;
    type Transcription;
    type ModelListing;
}
