# Figures Directory

Place your figures (images, plots, diagrams) in this directory.

## Supported Formats

- **PDF** (recommended for vector graphics like plots)
- **PNG** (for screenshots, photos)
- **JPG** (for photos)

## Including Figures in Your Paper

In your `.tex` files, reference figures like this:

```latex
\begin{figure}
  \centering
  \includegraphics[width=\linewidth]{figures/your-figure.pdf}
  \caption{Your descriptive caption here}
  \label{fig:yourfigure}
\end{figure}
```

Then reference in text: `As shown in Figure~\ref{fig:yourfigure}...`

## Tips

- Use descriptive filenames: `editor-activity-timeline.pdf` not `fig1.pdf`
- For plots from Python/R, export as PDF for best quality
- Keep original high-resolution versions
- Ensure figures are readable when printed in grayscale

