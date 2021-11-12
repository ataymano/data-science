def plot_loss(job, fig, ax):
    fig.suptitle('Loss')
    job.loss_table['loss'].plot(ax=ax)
